import sys
from datetime import datetime, timedelta, timezone
import httpx

URL = 'http://127.0.0.1:8000/webhook/zabbix'

SCENARIOS = {
    'ont-los': (
        [f'ONT-0{i}' for i in range(1, 6)],
        'ONT LOS (sinyal hilang)',
        4,
    ),
    'olt-down': (['OLT-01'], 'OLT tidak dapat dijangkau', 5),
    'b2b-loss': (['B2B-ACME'], 'Link pelanggan B2B putus', 3),
    'iptv-degrade': (['IPTV-HEAD'], 'Stream IPTV degradasi', 3),
}


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


name = sys.argv[1]
recover = '--recover' in sys.argv
hosts, trigger, severity = SCENARIOS[name]
fault_start = now() - timedelta(minutes=3)

for h in hosts:
    body = {
        'event_id': f'{name}-{h}',
        'event_value': 0 if recover else 1,
        'trigger_name': trigger,
        'host': h,
        'severity': severity,
        'time': now().isoformat(),
        'fault_started_at': fault_start.isoformat(),
    }
    r = httpx.post(URL, json=body)
    print(h, r.status_code, r.json())