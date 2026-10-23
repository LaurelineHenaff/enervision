import os

from dotenv import load_dotenv

load_dotenv()

# URL interne de l'école par défaut, comme dans l'API : l'URL publique demande une authentification
MOCK_API_URL = (os.getenv("MOCK_API_URL") or "http://10.43.43.80:8000").rstrip("/")
MOCK_API_USERNAME = os.getenv("MOCK_API_USERNAME")
MOCK_API_PASSWORD = os.getenv("MOCK_API_PASSWORD")
