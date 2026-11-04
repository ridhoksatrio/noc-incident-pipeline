TOPO = {
    'OLT-01': {
        'parent': None, 'customers': 40,
        'service': 'FTTH', 'sla_target': 99.5
    },
    'ONT-01': {'parent': 'OLT-01', 'customers': 1, 'service': 'FTTH'},
    'ONT-02': {'parent': 'OLT-01', 'customers': 1, 'service': 'FTTH'},
    'ONT-03': {'parent': 'OLT-01', 'customers': 1, 'service': 'FTTH'},
    'ONT-04': {'parent': 'OLT-01', 'customers': 1, 'service': 'FTTH'},
    'ONT-05': {'parent': 'OLT-01', 'customers': 1, 'service': 'FTTH'},
    'OLT-02': {
        'parent': None, 'customers': 24,
        'service': 'FTTH', 'sla_target': 99.5
    },
    'ONT-06': {'parent': 'OLT-02', 'customers': 1, 'service': 'FTTH'},
    'ONT-07': {'parent': 'OLT-02', 'customers': 1, 'service': 'FTTH'},
    'ONT-08': {'parent': 'OLT-02', 'customers': 1, 'service': 'FTTH'},
    'IPTV-HEAD': {
        'parent': None, 'customers': 60,
        'service': 'IPTV', 'sla_target': 99.5
    },
    'B2B-ACME': {
        'parent': None, 'customers': 1,
        'service': 'B2B', 'sla_target': 99.9
    },
}