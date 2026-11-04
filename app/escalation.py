MATRIX = {
    'FTTH': {
        'L2': 'NOC L2 - Access Network',
        'L3': 'Engineer Jaringan Akses (on-call)',
    },
    'IPTV': {
        'L2': 'NOC L2 - Video/IPTV',
        'L3': 'Engineer Headend (on-call)',
    },
    'B2B': {
        'L2': 'NOC L2 - Enterprise',
        'L3': 'Enterprise Engineer (on-call)',
    },
}

ALLOWED = {
    'open': {'acknowledged', 'escalated', 'resolved'},
    'acknowledged': {'escalated', 'resolved'},
    'escalated': {'acknowledged', 'resolved'},
    'resolved': {'closed', 'open'},
    'closed': set(),
}


def render(inc, target='L2', checked=''):
    t = MATRIX.get(inc.service, {}).get(target, 'NOC L2')
    return f'''[{inc.priority}] [{inc.service}] - {inc.root_cause_host}
Kepada : {t}
Kode : {inc.code}
Mulai : {inc.detected_at:%Y-%m-%d %H:%M} UTC
Dampak : {inc.customers_affected} pelanggan
Gejala : {inc.title}
Sudah dicek: {checked or '-'}
Mohon : investigasi dan tindakan lanjut'''