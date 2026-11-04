def alarm(client, host, sev=4, value=1, name='ALARM'):
    r = client.post('/webhook/zabbix', json={
        'event_id': f'{host}-{name}',
        'event_value': value,
        'trigger_name': name,
        'host': host,
        'severity': sev,
    })
    return r.json()


def test_five_alarms_become_one_incident(client):
    codes = {alarm(client, f'ONT-0{i}')['code'] for i in range(1, 6)}
    assert len(codes) == 1
    inc = client.get(f'/incidents/{codes.pop()}').json()
    assert inc['priority'] == 'P1'
    assert inc['customers_affected'] == 5


def test_b2b_sev3_is_p2(client):
    assert alarm(client, 'B2B-ACME', sev=3)['priority'] == 'P2'


def test_invalid_transition_rejected(client):
    code = alarm(client, 'IPTV-HEAD', sev=3)['code']
    r = client.post(
        f'/incidents/{code}/transition', params={'to': 'closed'}
    )
    assert r.status_code == 409


def test_auto_resolve_on_recovery(client):
    alarm(client, 'IPTV-HEAD', sev=3)
    r = alarm(client, 'IPTV-HEAD', sev=3, value=0)
    assert r['status'] == 'resolved'


def test_unknown_host_rejected(client):
    r = client.post('/webhook/zabbix', json={
        'event_id': 'x',
        'trigger_name': 't',
        'host': 'TIDAK-ADA',
        'severity': 3,
    })
    assert r.status_code == 422