from datetime import datetime
from typing import Literal

from dotenv import load_dotenv

# Muat konfigurasi .env sebelum mengimpor modul aplikasi.
load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, DATASET_ID
from app.livlab import METRICS, dataset_path, request_livlab, round_metrics
from batch_api import router as batch_router

app = FastAPI(
    title='Smart Garden Research API',
    version='2.0.0',
    description='FastAPI proxy aman untuk Research Data API LivLab (tanpa data dummy).',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['*'],
)

# Endpoint kontrol batch ESP32; endpoint LivLab tetap dipertahankan.
app.include_router(batch_router)


def iso_time(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise HTTPException(
            status_code=422,
            detail='Tanggal harus ISO 8601 dengan timezone, contoh 2026-11-19T00:00:00Z',
        )
    return value.isoformat()


def time_params(from_time: datetime | None, to_time: datetime | None) -> dict:
    if from_time and to_time and from_time > to_time:
        raise HTTPException(status_code=422, detail='from tidak boleh lebih besar dari to')
    return {'from': iso_time(from_time), 'to': iso_time(to_time)}


@app.get('/')
async def home():
    return {'status': 'ok', 'service': 'Smart Garden FastAPI', 'docs': '/docs'}


@app.get('/api/health')
async def health():
    return {
        'status': 'ok',
        'dataset_id': DATASET_ID,
        'note': 'Health lokal, bukan status koneksi LivLab',
    }


@app.get('/api/metrics')
async def metrics():
    return {
        'dataset_id': DATASET_ID,
        'total': len(METRICS),
        'metrics': [{'name': k, 'unit': v} for k, v in METRICS.items()],
        'source': 'registered_contract',
    }


@app.get('/api/datasets')
async def datasets():
    return await request_livlab('/datasets')


@app.get('/api/dataset')
async def dataset():
    return await request_livlab(dataset_path())


@app.get('/api/livlab/status')
async def livlab_status():
    metadata = await request_livlab(dataset_path())
    latest = await request_livlab(dataset_path('/latest'), {'limit': 1})
    data = latest.get('data') or {}
    return {
        'reachable': True,
        'dataset_id': DATASET_ID,
        'dataset': metadata.get('data'),
        'latest_event_available': bool(data.get('items')),
        'freshness': data.get('freshness'),
    }


@app.get('/api/latest')
async def latest(limit: int = Query(10, ge=1, le=100), rounded: bool = False):
    result = await request_livlab(dataset_path('/latest'), {'limit': limit})
    return round_metrics(result) if rounded else result


@app.get('/api/history')
async def history(
    from_time: datetime | None = Query(None, alias='from'),
    to_time: datetime | None = Query(None, alias='to'),
    metric: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    sort: Literal['asc', 'desc'] = 'desc',
    cursor: str | None = None,
    rounded: bool = False,
):
    if metric is not None and metric not in METRICS:
        raise HTTPException(status_code=422, detail='Metric tidak terdaftar')
    params = {
        **time_params(from_time, to_time),
        'metric': metric,
        'page': page,
        'page_size': page_size,
        'sort': sort,
        'cursor': cursor,
    }
    result = await request_livlab(dataset_path('/telemetry'), params)
    return round_metrics(result) if rounded else result


@app.get('/api/history/metrics')
async def history_metrics(
    from_time: datetime | None = Query(None, alias='from'),
    to_time: datetime | None = Query(None, alias='to'),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    sort: Literal['asc', 'desc'] = 'asc',
):
    params = {
        **time_params(from_time, to_time),
        'page': page,
        'page_size': page_size,
        'sort': sort,
    }
    return await request_livlab(dataset_path('/telemetry/metrics'), params)


@app.get('/api/series')
async def series(
    metric: str,
    from_time: datetime | None = Query(None, alias='from'),
    to_time: datetime | None = Query(None, alias='to'),
    limit_points: int = Query(500, ge=1, le=2000),
):
    if metric not in METRICS:
        raise HTTPException(
            status_code=422,
            detail='Metric tidak terdaftar (nama case-sensitive)',
        )
    params = {
        **time_params(from_time, to_time),
        'metric': metric,
        'limit_points': limit_points,
    }
    return await request_livlab(dataset_path('/series'), params)


@app.get('/api/stream')
async def stream(
    from_time: datetime | None = Query(None, alias='from'),
    to_time: datetime | None = Query(None, alias='to'),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    # JSON polling, NOT SSE. Cap to protect backend; direct Node may return 502.
    params = {
        **time_params(from_time, to_time),
        'limit': limit,
        'cursor': cursor,
    }
    return await request_livlab(dataset_path('/stream'), params)
