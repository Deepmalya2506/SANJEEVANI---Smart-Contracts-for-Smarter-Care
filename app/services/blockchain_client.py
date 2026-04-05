import requests
from app.core.config import settings

def create_loan(data):
    res = requests.post(
        f"{settings.BLOCKCHAIN_URL}/blockchain/create-loan",
        json=data
    )
    return res.json()