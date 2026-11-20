"""Tambahkan ke FastAPI: from batch_api import router as batch_router; app.include_router(batch_router)."""
import os
import re
import ipaddress
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/esp32", tags=["ESP32 batch"])

class BatchPayload(BaseModel):
    batch: int = Field(ge=1, le=999999)
    tanggal_tanam: str
    fase: int = Field(default=0, ge=0, le=2)

def esp32_url():
    host = os.getenv("ESP32_HOST", "").strip()
    key = os.getenv("ESP32_API_KEY", "")
    if not host or len(key) < 32:
        raise HTTPException(503, "Set ESP32_HOST dan ESP32_API_KEY di backend .env")
    try:
        address = ipaddress.ip_address(host)
        if not address.is_private:
            raise ValueError("ESP32_HOST harus IP jaringan lokal")
    except ValueError:
        raise HTTPException(503, "ESP32_HOST harus alamat IPv4/IPv6 privat, contoh 192.168.1.50")
    return f"http://{host}:80", key

async def relay(method, path, payload=None, params=None):
    base, key = esp32_url()
    try:
        async with httpx.AsyncClient(timeout=8.0, trust_env=False) as client:
            res = await client.request(method, base+path, json=payload, params=params,
                                       headers={"X-API-Key":key})
        try: body = res.json()
        except ValueError: body = {"detail":res.text[:200]}
        if res.status_code >= 400:
            raise HTTPException(res.status_code, body.get("detail", "ESP32 menolak perintah"))
        return body
    except httpx.RequestError as exc:
        raise HTTPException(502, f"ESP32 tidak dapat dihubungi: {type(exc).__name__}")

@router.get("/status")
async def get_status():
    return await relay("GET", "/api/status")

@router.post("/batch")
async def add_batch(data: BatchPayload):
    return await write_batch(data, "POST")

@router.put("/batch")
async def edit_batch(data: BatchPayload):
    return await write_batch(data, "PUT")

async def write_batch(data, method):
    date = data.tanggal_tanam
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise HTTPException(422, "Tanggal harus YYYY-MM-DD")
    from datetime import date as Date
    try:
        parsed = Date.fromisoformat(date)
    except ValueError:
        raise HTTPException(422, "Tanggal tidak valid")
    if not 2024 <= parsed.year <= 2100:
        raise HTTPException(422, "Tahun harus 2024–2100")
    return await relay(method, "/api/batch", {
        "batch":data.batch, "tanggal_tanam":int(date.replace("-","")), "fase":data.fase
    })

@router.delete("/batch/{batch_number}")
async def delete_batch(batch_number: int):
    if not 1 <= batch_number <= 999999:
        raise HTTPException(422, "Batch tidak valid")
    return await relay("DELETE", "/api/batch", params={"batch":batch_number})
