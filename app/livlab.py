import httpx
from fastapi import HTTPException
from app.config import API_KEY, BASE_URL, DATASET_ID, TIMEOUT

METRICS = {
    'tds': 'ppm', 'Suhu': '°C', 'PH': 'pH', 'Water level': 'cm',
    'fase_pertumbuhan': 'code', 'setpoint': 'ppm', 'error': 'ppm',
    'output_pid': 'code', 'status_pompa_a': 'code', 'status_pompa_b': 'code',
    'status_pengaduk': 'code', 'durasi_pompa': 'detik',
    'kondisi_sistem': 'code', 'nama_batch': 'code',
    'tanggal_tanam': 'tanggal', 'umur_tanaman': 'hari',
    'status batch': 'code', 'response_time': 'detik',
}


def dataset_path(suffix: str = '') -> str:
    return f'/datasets/{DATASET_ID}{suffix}'


async def request_livlab(path: str, params: dict | None = None) -> dict:
    if not API_KEY or API_KEY == 'ISI_API_KEY_KAMU':
        raise HTTPException(status_code=503, detail='LIVLAB_API_KEY belum diisi pada .env')
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT, follow_redirects=False) as client:
            response = await client.get(path, headers={'X-API-Key': API_KEY, 'Accept': 'application/json'}, params={k: v for k, v in (params or {}).items() if v is not None})
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail='LivLab API timeout')
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail='Tidak dapat menghubungi LivLab API')

    if response.status_code >= 400:
        headers = {}
        if response.status_code == 429 and response.headers.get('Retry-After'):
            headers['Retry-After'] = response.headers['Retry-After']
        # Do not expose upstream internals or credentials in public errors.
        raise HTTPException(status_code=response.status_code if 400 <= response.status_code <= 599 else 502,
                            detail=f'LivLab API mengembalikan HTTP {response.status_code}', headers=headers)
    try:
        return response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail='Respons LivLab bukan JSON valid')


def round_metrics(payload: dict) -> dict:
    """Only for display: preserve original telemetry precision by default."""
    import copy
    output = copy.deepcopy(payload)
    data = output.get('data')
    if isinstance(data, dict):
        for item in data.get('items', []):
            if isinstance(item, dict):
                metrics = item.get('metrics', {})
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        if isinstance(value, (float, int)) and not isinstance(value, bool):
                            metrics[key] = round(value)
                for detail in item.get('metric_details', []):
                    if isinstance(detail, dict) and isinstance(detail.get('value'), (float, int)) and not isinstance(detail['value'], bool):
                        detail['value'] = round(detail['value'])
    return output
