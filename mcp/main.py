from fastapi import FastAPI
from mcp.chain_listener import listen
import threading

app = FastAPI()

@app.get("/")
def root():
    return {"service": "Sanjeevani MCP Running"}

def start_listener():
    listen()

thread = threading.Thread(target=start_listener)
thread.start()