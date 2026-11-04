from datetime import timedelta
from .models import Incident
from .topology import TOPO

ACTIVE = ['open', 'acknowledged', 'escalated']
WINDOW = timedelta(minutes=30)


def root_of(host):
    while TOPO[host].get('parent'):
        host = TOPO[host]['parent']
    return host


def find_open_incident(db, host, now):
    root = root_of(host)
    return (
        db.query(Incident)
        .filter(
            Incident.root_cause_host == root,
            Incident.status.in_(ACTIVE),
            Incident.detected_at >= now - WINDOW,
        )
        .first()
    )


def customers_affected(incident):
    hosts = {a.host for a in incident.alarms}
    root = incident.root_cause_host
    if root in hosts:
        return TOPO[root]['customers']
    return sum(TOPO[h]['customers'] for h in hosts)


def priority_for(service, severity, customers):
    if severity >= 5 or customers >= 5:
        return 'P1'
    if severity >= 4 or (service == 'B2B' and severity >= 3):
        return 'P2'
    if severity >= 3:
        return 'P3'
    return 'P4'