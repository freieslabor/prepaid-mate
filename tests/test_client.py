def test_client(flask_server, scanner_client):
    expected_out = [
        'account barcode: 0016027465',
        'account "0016027465" ordered "42254300"'
    ]
    _, proc = scanner_client
    for expect in expected_out:
        out = proc.stderr.readline().decode('utf-8')
        assert out.strip().endswith(expect), 'unexpected: {}'.format(out)

    print(proc.stderr.readline()) # Calling
    print(proc.stderr.readline()) # callback successfull
