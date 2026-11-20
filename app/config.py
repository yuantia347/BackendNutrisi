import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('LIVLAB_BASE_URL', 'https://research-data-gateway.myact.my.id/api/v1/external').rstrip('/')
DATASET_ID = os.getenv('LIVLAB_DATASET_ID', 'dst_b102638a274e3714')
API_KEY = os.getenv('LIVLAB_API_KEY', '')
TIMEOUT = float(os.getenv('LIVLAB_TIMEOUT_SECONDS', '15'))
CORS_ORIGINS = [s.strip() for s in os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',') if s.strip()]
