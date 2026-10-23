import os

from dotenv import load_dotenv

load_dotenv()

MOCK_API_URL = os.getenv("MOCK_API_URL")
MOCK_API_USERNAME = os.getenv("MOCK_API_USERNAME")
MOCK_API_PASSWORD = os.getenv("MOCK_API_PASSWORD")
