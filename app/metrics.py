from .models import Incident
from .topology import TOPO


def _mins(a, b):
    return (b - a).total_seconds() / 60


def _in_window(db, start, end):
    return (
        db.query(Incident)
        .filter(Incident.detected_at >= start, Incident.detected_at < end)
        .all()
    )


def mttd(db, start, end):
    v = [
        _mins(i.fault_started_at, i.detected_at)
        for i in _in_window(db, start, end)
        if i.fault_started_at
    ]
    return round(sum(v) / len(v), 1) if v else 0.0


def mttr(db, start, end):
    v = [
        _mins(i.detected_at, i.resolved_at)
        for i in _in_window(db, start, end)
        if i.resolved_at
    ]
    return round(sum(v) / len(v), 1) if v else 0.0


def availability(db, host, start, end):
    period = _mins(start, end)
    down = 0.0
    for i in _in_window(db, start, end):
        if i.root_cause_host == host and i.priority in ('P1', 'P2'):
            t0 = max(i.fault_started_at or i.detected_at, start)
            t1 = min(i.resolved_at or end, end)
            down += max(_mins(t0, t1), 0)
    return round((period - down) / period * 100, 3)


def _duration(i, end):
    return round(_mins(i.detected_at, i.resolved_at or end), 1)


def summary(db, start, end):
    rows = _in_window(db, start, end)
    services = []
    for host, node in TOPO.items():
        if node.get('parent') is None:
            a = availability(db, host, start, end)
            services.append({
                'host': host,
                'service': node['service'],
                'availability': a,
                'target': node['sla_target'],
                'breach': a < node['sla_target'],
            })
    top = sorted(
        rows, key=lambda i: _duration(i, end), reverse=True
    )[:5]
    return {
        'total': len(rows),
        'by_priority': {
            p: sum(1 for i in rows if i.priority == p)
            for p in ('P1', 'P2', 'P3', 'P4')
        },
        'mttd': mttd(db, start, end),
        'mttr': mttr(db, start, end),
        'services': services,
        'top': [
            {
                'code': i.code,
                'host': i.root_cause_host,
                'priority': i.priority,
                'duration': _duration(i, end),
                'customers': i.customers_affected,
                'rca': i.rca or '-',
            }
            for i in top
        ],
    }