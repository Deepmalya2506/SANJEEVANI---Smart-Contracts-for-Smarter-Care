import requests

MCP_URL = "http://127.0.0.1:9001"

def call_dispatch():
    return requests.post(
        f"{MCP_URL}/tool/dispatch_agent",
        json={
            "equipment_type": 1,
            "quantity": 1,
            "location": {
                "lat": 25.2,
                "lon": 27.2
            }
        }
    ).json()

print(call_dispatch())