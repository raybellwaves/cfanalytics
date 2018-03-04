import xarray as xr


def test_utils():
    expected = xr.Dataset({'wodscompleted': 3})
    wodscompleted = 3
    actual = xr.Dataset()
    actual['wodscompleted'] = wodscompleted
    assert expected.data_vars == actual.data_vars