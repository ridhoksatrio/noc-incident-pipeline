from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import correlation as corr
from .database import Base, engine, get_db
from .escalation import ALLOWED, render
from .metrics import summary
from .models import Alarm, Incident, TimelineEvent, utcnow
from .topology import TOPO

Base.metadata.create_all(bind=engine)
app = FastAPI(title='NOC Incident Pipeline (lab simulasi)')


class AlarmIn(BaseModel):
    event_id: str
    event_value: int = 1
    trigger_name: str
    host: str
    severity: int = Field(ge=0, le=5)
    time: datetime | None = None
    fault_started_at: datetime | None = None


def naive_utc(dt):
    if dt is not None and dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def log(db, inc, actor, action, note=''):
    db.add(TimelineEvent(
        incident=inc, at=utcnow(), actor=actor,
        action=action, note=note
    ))


def get_incident(db, code):
    inc = db.query(Incident).filter_by(code=code).first()
    if not inc:
        raise HTTPException(404, 'insiden tidak ditemukan')
    return inc


def to_dict(inc, detail=False):
    d = {
        'code': inc.code,
        'title': inc.title,
        'service': inc.service,
        'root_cause_host': inc.root_cause_host,
        'priority': inc.priority,
        'status': inc.status,
        'customers_affected': inc.customers_affected,
        'detected_at': inc.detected_at,
        'rca': inc.rca,
    }
    if detail:
        d['alarms'] = [
            {
                'host': a.host, 'trigger': a.trigger_name,
                'severity': a.severity, 'cleared': a.cleared,
            }
            for a in inc.alarms
        ]
        d['timeline'] = [
            {
                'at': t.at, 'actor': t.actor,
                'action': t.action, 'note': t.note,
            }
            for t in sorted(inc.timeline, key=lambda t: t.id)
        ]
    return d


def new_code(db, now):
    n = (
        db.query(Incident)
        .filter(Incident.simulated.is_(False))
        .count() + 1
    )
    return f'INC-{now:%Y%m%d}-{n:04d}'


@app.post('/webhook/zabbix')
def webhook(a: AlarmIn, db: Session = Depends(get_db)):
    if a.host not in TOPO:
        raise HTTPException(422, f'host {a.host} tidak ada di topology')
    now = naive_utc(a.time) or utcnow()
    if a.event_value == 0:
        return handle_recovery(db, a, now)

    inc = corr.find_open_incident(db, a.host, now)
    created = inc is None
    if created:
        root = corr.root_of(a.host)
        inc = Incident(
            code=new_code(db, now),
            title=a.trigger_name,
            service=TOPO[root]['service'],
            root_cause_host=root,
            status='open',
            detected_at=now,
            fault_started_at=naive_utc(a.fault_started_at) or now,
        )
        db.add(inc)
        db.flush()
        log(db, inc, 'system', 'CREATED', a.trigger_name)

    db.add(Alarm(
        incident=inc, host=a.host, trigger_name=a.trigger_name,
        severity=a.severity, event_id=a.event_id, received_at=now,
    ))
    db.flush()

    inc.customers_affected = corr.customers_affected(inc)
    sev = max(x.severity for x in inc.alarms)
    inc.priority = corr.priority_for(inc.service, sev, inc.customers_affected)

    if not created:
        log(db, inc, 'system', 'ALARM_ADDED',
            f'{a.host}: {a.trigger_name}')

    db.commit()
    return {
        'code': inc.code,
        'priority': inc.priority,
        'new_incident': created,
        'customers_affected': inc.customers_affected,
        'alarms': len(inc.alarms),
    }


def handle_recovery(db, a, now):
    root = corr.root_of(a.host)
    inc = (
        db.query(Incident)
        .filter(
            Incident.root_cause_host == root,
            Incident.status.in_(corr.ACTIVE),
        )
        .first()
    )
    if not inc:
        return {'ignored': 'tidak ada insiden aktif'}

    for al in inc.alarms:
        if al.host == a.host:
            al.cleared = True
            log(db, inc, 'system', 'ALARM_CLEARED', a.host)

    if all(al.cleared for al in inc.alarms):
        inc.status = 'resolved'
        inc.resolved_at = now
        log(db, inc, 'system', 'AUTO_RESOLVED', 'semua alarm clear')

    db.commit()
    return {'code': inc.code, 'status': inc.status}


@app.get('/incidents')
def list_incidents(
    status: str | None = None, db: Session = Depends(get_db)
):
    q = db.query(Incident)
    if status:
        q = q.filter(Incident.status == status)
    return [
        to_dict(i)
        for i in q.order_by(Incident.id.desc()).limit(100)
    ]


@app.get('/incidents/{code}')
def incident_detail(code: str, db: Session = Depends(get_db)):
    return to_dict(get_incident(db, code), detail=True)


@app.post('/incidents/{code}/transition')
def transition(
    code: str,
    to: str,
    actor: str = 'noc-intern',
    note: str = '',
    db: Session = Depends(get_db),
):
    inc = get_incident(db, code)
    if to not in ALLOWED.get(inc.status, set()):
        raise HTTPException(409, f'{inc.status} -> {to} tidak valid')
    if to == 'closed' and not note:
        raise HTTPException(
            422, 'menutup insiden wajib mengisi RCA di parameter note'
        )

    now = utcnow()
    inc.status = to
    if to == 'acknowledged':
        inc.acknowledged_at = now
    if to == 'resolved':
        inc.resolved_at = now
    if to == 'closed':
        inc.closed_at = now
        inc.rca = note

    log(db, inc, actor, to.upper(), note)
    db.commit()
    return {'code': code, 'status': inc.status}


@app.get('/incidents/{code}/escalation')
def escalation(
    code: str,
    target: str = 'L2',
    checked: str = '',
    db: Session = Depends(get_db),
):
    return {
        'message': render(get_incident(db, code), target, checked)
    }


@app.get('/metrics/summary')
def metrics_summary(days: int = 7, db: Session = Depends(get_db)):
    end = utcnow()
    return summary(db, end - timedelta(days=days), end)