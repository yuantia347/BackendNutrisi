# Smart Garden FastAPI v2 — dari nol

Backend monitoring Research Data API LivLab. Tidak menggunakan Flask, InfluxDB lokal, maupun data dummy.

## Persiapan (Windows PowerShell)

1. Ekstrak ZIP, buka folder `smartgarden_fastapi_v2` di VS Code.
2. Pastikan Python 3.10+ terinstal: `py --version`.
3. Buat environment: `py -m venv .venv`.
4. Install tanpa aktivasi: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
5. Salin `.env.example` menjadi `.env`: `Copy-Item .env.example .env`.
6. Isi `LIVLAB_API_KEY` dengan key resmi Research API Keys; jangan kirim ke chat, jangan commit ke Git.
7. Jalankan: `.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`.
8. Buka `http://127.0.0.1:8000/docs` untuk mencoba endpoint.

## Urutan pengujian

- `http://127.0.0.1:8000/api/health` — server lokal sehat (tidak mengecek LivLab)
- `http://127.0.0.1:8000/api/metrics` — daftar 18 metric dari kontrak
- `http://127.0.0.1:8000/api/datasets` — discovery, memastikan API key dan grant
- `http://127.0.0.1:8000/api/dataset` — metadata dataset
- `http://127.0.0.1:8000/api/livlab/status` — metadata, latest event dan freshness
- `http://127.0.0.1:8000/api/latest?limit=1` — satu event terbaru, presisi asli
- `http://127.0.0.1:8000/api/latest?limit=1&rounded=true` — tampilan angka dibulatkan
- `http://127.0.0.1:8000/api/history?page=1&page_size=10` — 10 event history
- `http://127.0.0.1:8000/api/history/metrics?page_size=10` — tabular projection
- `http://127.0.0.1:8000/api/series?metric=tds&limit_points=100` — grafik TDS
- `http://127.0.0.1:8000/api/series?metric=PH` — grafik pH (huruf besar)
- `http://127.0.0.1:8000/api/stream?limit=10` — JSON polling langsung ke Edge Node, bukan SSE; bisa HTTP 502 jika upstream Node bermasalah

Filter waktu (timezone wajib): `/api/history?from=2026-11-19T00:00:00Z&to=2026-11-19T23:59:59Z&page_size=10`.

## Ketentuan penting

- Data ESP32 mengalir melalui MQTT → LivLab ingestion → cloud sync → Research Data API → backend ini. ESP32 tidak mengirim langsung ke backend ini.
- Semua request eksternal menggunakan header `X-API-Key` **di sisi server**. Browser hanya mengakses backend FastAPI.
- `metrics` pada respons `/latest` dan `/history` adalah objek nama metric → nilai, dengan kapitalisasi dan spasi persis seperti kontrak. `metric_details` berisi unit.
- `rounded=true` hanya untuk tampilan. Untuk analisis pH, PID, dan grafik gunakan nilai asli.
- `freshness` dapat null/stale; `items` kosong bukan otomatis berarti ESP32 offline.
- `/stream` adalah JSON polling, bukan websocket/SSE, dan format responsnya berbeda dari `/latest`.
- HTTP 401: cek key; HTTP 403/404: cek grant/dataset; HTTP 429: kurangi polling dan hormati `Retry-After`; HTTP 502: cek upstream; HTTP 504: timeout.
- Belum ada endpoint pengiriman perintah START/STOP/BATCH/pompa karena dokumentasi Research Data API hanya menyediakan pembacaan.
- Tes lokal: `.\.venv\Scripts\python.exe -m pytest -q`.

## Integrasi frontend

Frontend melakukan GET ke `http://localhost:8000/api/latest?limit=1`, membaca `data.items[0].metrics` dan `data.freshness`. Gunakan polling wajar (mis. 10–30 detik) dan tangani 429; jangan expose API key ke frontend.
