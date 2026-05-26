"""
wrapper.py — Sanjeevani MCP Server
Endpoints:
  POST /chat          — main chat (session-aware, returns structured result)
  GET  /chat/stream   — SSE stream for live stage notifications
  DELETE /session     — clear a session
  GET  /health        — health check
"""

import asyncio
import json
import uuid
from typing import Optional

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from mcp_server.main import run_agent, clear_session

app = FastAPI(title="Sanjeevani MCP Server", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── SSE notification queues (session_id → asyncio.Queue) ─────────────────────
_notification_queues: dict[str, asyncio.Queue] = {}

def get_queue(session_id: str) -> asyncio.Queue:
    if session_id not in _notification_queues:
        _notification_queues[session_id] = asyncio.Queue()
    return _notification_queues[session_id]


# ── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query:       str
    session_id:  Optional[str] = None   # If None, a new session is created
    hospital_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id:        str
    reply:             str
    approval_required: bool = False
    loan_proposal:     Optional[dict] = None
    map_url:           Optional[str]  = None
    tx_hash:           Optional[str]  = None
    loan_id:           Optional[int]  = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "Sanjeevani MCP"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Create or reuse session
    session_id = req.session_id or str(uuid.uuid4())

    # Notification callback — puts messages into the SSE queue
    loop = asyncio.new_event_loop()

    notifications = []
    def notify(msg: str):
        notifications.append(msg)
        # Also push to SSE queue if a stream listener is active
        q = _notification_queues.get(session_id)
        if q:
            try:
                q.put_nowait(msg)
            except Exception:
                pass

    result = run_agent(
        user_query=req.query,
        session_id=session_id,
        hospital_id=req.hospital_id,
        notify=notify,
    )

    return ChatResponse(
        session_id        = session_id,
        reply             = result["reply"],
        approval_required = result.get("approval_required", False),
        loan_proposal     = result.get("loan_proposal"),
        map_url           = result.get("map_url"),
        tx_hash           = result.get("tx_hash"),
        loan_id           = result.get("loan_id"),
    )


@app.get("/chat/stream/{session_id}")
async def chat_stream(session_id: str):
    """
    SSE endpoint — connect to this before sending a /chat request.
    The frontend receives stage notifications in real time.
    """
    queue = get_queue(session_id)

    async def event_generator():
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps({'notification': msg})}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"  # keep connection alive

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    clear_session(session_id)
    _notification_queues.pop(session_id, None)
    return {"cleared": session_id}


@app.get("/map-dialog")
def map_dialog(map_url: str):
    """
    Returns a self-contained HTML page that embeds the OSM route map in an
    iframe. The frontend opens this in a modal/dialog overlay.
    Designed as a floating panel — not a full page navigation.
    """
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Sanjeevani Route Map</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: 'Segoe UI', sans-serif;
    background: #0f1117;
    color: #e2e8f0;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: #1a1f2e;
    border-bottom: 1px solid #2d3748;
    flex-shrink: 0;
  }}
  header .dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: #48bb78; box-shadow: 0 0 6px #48bb78;
  }}
  header h2 {{ font-size: 14px; font-weight: 600; color: #90cdf4; }}
  header span {{ font-size: 12px; color: #718096; margin-left: auto; }}
  iframe {{
    flex: 1;
    width: 100%;
    border: none;
  }}
  .error {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 12px;
    color: #fc8181;
  }}
</style>
</head>
<body>
  <header>
    <div class="dot"></div>
    <h2>🗺️ Sanjeevani Route Map</h2>
    <span>Powered by OpenStreetMap</span>
  </header>
  <iframe
    src="{map_url}"
    title="Route Map"
    loading="lazy"
    sandbox="allow-scripts allow-same-origin"
    onerror="document.querySelector('iframe').style.display='none';
             document.querySelector('.error').style.display='flex';">
  </iframe>
  <div class="error" style="display:none">
    <p>⚠️ Unable to load map. GIS server may be offline.</p>
    <a href="{map_url}" target="_blank" style="color:#90cdf4">Open in new tab →</a>
  </div>
</body>
</html>"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(html)