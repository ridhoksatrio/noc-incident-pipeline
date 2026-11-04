import random
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import correlation as corr
from app.database import Base, SessionLocal, engine
from app.models import Alarm, Incident, utcnow
from app.topology import TOPO


def run(n=40, days=28, seed=42):
    rnd = random.Random(seed)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    for old in db.query(Incident).filter(Incident.simulated.is_(True)).all():
        db.delete(old)
    db.commit()

    roots = [h for h, node in TOPO.items() if node.get('parent') is None]
    end = utcnow()

    for k in range(n):
        host = rnd.choice(roots)
        node = TOPO[host]
        start = end - timedelta(minutes=rnd.randint(180, days * 24 * 60))
        detected = start + timedelta(minutes=rnd.randint(1, 6))
        resolved = detected + timedelta(minutes=rnd.randint(5, 60))
        sev = rnd.choice([4, 5])

        inc = Incident(
            code=f'SIM-{k + 1:04d}',
            title=f'[LAB-SIMULATED] Gangguan {host}',
            service=node['service'],
            root_cause_host=host,
            priority=corr.priority_for(
                node['service'], sev, node['customers']
            ),
            status='closed',
            customers_affected=node['customers'],
            fault_started_at=start,
            detected_at=detected,
            acknowledged_at=detected + timedelta(minutes=2),
            resolved_at=resolved,
            closed_at=resolved + timedelta(minutes=10),
            rca='LAB-SIMULATED: data simulasi, bukan kejadian nyata',
            simulated=True,
        )
        inc.alarms.append(Alarm(
            host=host,
            trigger_name='LAB-SIMULATED',
            severity=sev,
            event_id=f'sim-{k}',
            received_at=detected,
            cleared=True,
        ))
        db.add(inc)

    db.commit()
    db.close()
    print(f'{n} insiden simulasi dibuat')


if __name__ == '__main__':
    run()