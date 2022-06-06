def assert_spreadsheets_equal(expect, got):
    es = expect.active
    gs = got.active
    grows = list(gs.values)
    for row in es.values:
        assert grows[0] == row
        grows = grows[1:]
    assert len(grows) == 0
