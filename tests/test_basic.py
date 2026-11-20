from datetime import datetime
from fastapi import HTTPException
from app.livlab import METRICS, round_metrics
from main import iso_time, time_params


def test_metrics_count():
    assert len(METRICS) == 18
    assert METRICS['status batch'] == 'code'


def test_rounding_does_not_mutate_source():
    source = {'data': {'items': [{'metrics': {'PH': 5.71, 'tds': 1094.38}, 'metric_details': [{'name': 'PH', 'value': 5.71}]}]}}
    output = round_metrics(source)
    assert output['data']['items'][0]['metrics']['PH'] == 6
    assert source['data']['items'][0]['metrics']['PH'] == 5.71


def test_timezone_required():
    try:
        iso_time(datetime(2026, 11, 19))
        assert False
    except HTTPException as exc:
        assert exc.status_code == 422


def test_time_order():
    try:
        time_params(datetime.fromisoformat('2026-11-20T00:00:00+00:00'), datetime.fromisoformat('2026-11-19T00:00:00+00:00'))
        assert False
    except HTTPException as exc:
        assert exc.status_code == 422
