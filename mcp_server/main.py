"""
main.py — Sanjeevani MCP Agent
Features:
  • Persistent per-session conversation memory
  • Stage-by-stage SSE progress notifications
  • Multi-step tool chaining (inventory → GIS → approval → dispatch → blockchain)
  • Human-in-the-loop approval gate before any loan / dispatch
  • Full smart-contract lifecycle via blockchain_tools
"""

import json
import requests
from groq import Groq
from dotenv import load_dotenv
import os
from typing import Optional, Callable

from app.core.database import hospital_collection
from mcp_server.blockchain_tools import (
    create_loan_on_chain,
    confirm_delivery_on_chain,
    settle_loan_on_chain,
    get_loan_status,
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─────────────────────────────────────────────
# SESSION MEMORY  (in-memory; swap for MongoDB for prod)
# ─────────────────────────────────────────────
_sessions: dict[str, list[dict]] = {}

def get_session(session_id: str) -> list[dict]:
    if session_id not in _sessions:
        _sessions[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    return _sessions[session_id]

def clear_session(session_id: str):
    _sessions.pop(session_id, None)


# ─────────────────────────────────────────────
# PENDING APPROVALS  (loan requests awaiting user confirm)
# ─────────────────────────────────────────────
_pending_approvals: dict[str, dict] = {}   # session_id → approval payload


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def get_hospital_location(hospital_id: str) -> Optional[dict]:
    hospital = hospital_collection.find_one({"id": hospital_id})
    return hospital["location"] if hospital else None

def safe_request(method: str, url: str, **kwargs) -> dict:
    try:
        res = requests.request(method, url, timeout=10, **kwargs)
        print(f"\n🌐  {method.upper()} {url}  →  {res.status_code}")
        print(f"    RAW: {res.text[:300]}")

        if res.status_code != 200:
            return {"error": f"{url} returned {res.status_code}", "raw": res.text}

        try:
            return res.json()
        except Exception:
            return {"error": "Invalid JSON", "raw": res.text}

    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# TOOL DEFINITIONS
# ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_inventory",
            "description": (
                "Search hospitals for a specific equipment type and minimum quantity. "
                "Pass hospital_id='all' to search across ALL hospitals. "
                "Returns list of hospitals that have the item available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hospital_id": {
                        "type": "string",
                        "description": "Hospital ID to search, or 'all' for all hospitals"
                    },
                    "equipment_type": {"type": "string"},
                    "quantity": {"type": "integer", "description": "Minimum quantity needed"}
                },
                "required": ["hospital_id", "equipment_type", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_hospitals",
            "description": "List all registered hospitals with their IDs, names, wallets and locations.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory",
            "description": "Get full inventory of a specific hospital.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hospital_id": {"type": "string"}
                },
                "required": ["hospital_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearest_hospitals",
            "description": (
                "Given a lat/lon origin, rank ALL hospitals by road distance and ETA. "
                "Returns best_hospital ID, ETA minutes, distance_km, and all_options list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"}
                },
                "required": ["lat", "lon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_route",
            "description": "Get driving route, distance and turn-by-turn directions between two points.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "object",
                        "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}},
                        "required": ["lat", "lon"]
                    },
                    "destination": {
                        "type": "object",
                        "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}},
                        "required": ["lat", "lon"]
                    }
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_route_map_url",
            "description": (
                "Returns a URL to an interactive OSM route map between two hospitals. "
                "Use this to give the user a visual map link after finding the best route."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_lat": {"type": "number"},
                    "origin_lon": {"type": "number"},
                    "dest_lat": {"type": "number"},
                    "dest_lon": {"type": "number"}
                },
                "required": ["origin_lat", "origin_lon", "dest_lat", "dest_lon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_isochrone",
            "description": "Get the area reachable from a point within a time limit (coverage radius).",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "time_limit_min": {"type": "integer"}
                },
                "required": ["lat", "lon", "time_limit_min"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch",
            "description": (
                "Record a dispatch event in the backend (inventory transfer). "
                "Call this ONLY after the user has explicitly approved the loan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_type": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "from_hospital_id": {"type": "string"},
                    "to_hospital_id": {"type": "string"},
                    "location": {
                        "type": "object",
                        "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}}
                    }
                },
                "required": ["equipment_type", "quantity", "from_hospital_id", "to_hospital_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_user_approval",
            "description": (
                "ALWAYS call this before creating a loan or dispatching equipment. "
                "Present a structured loan summary to the user and wait for their confirmation. "
                "Include all loan details so the user can make an informed decision."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "from_hospital_id":   {"type": "string"},
                    "from_hospital_name": {"type": "string"},
                    "to_hospital_id":     {"type": "string"},
                    "equipment_type":     {"type": "string"},
                    "quantity":           {"type": "integer"},
                    "duration_hours":     {"type": "integer"},
                    "distance_km":        {"type": "number"},
                    "eta_min":            {"type": "number"},
                    "route_map_url":      {"type": "string", "description": "OSM map URL if available"}
                },
                "required": [
                    "from_hospital_id", "from_hospital_name",
                    "equipment_type", "quantity", "duration_hours"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_blockchain_loan",
            "description": (
                "Create a loan on the Sanjeevani smart contract (Escrow). "
                "Call this ONLY after request_user_approval was accepted by the user. "
                "This locks funds in escrow and emits LoanCreated event on-chain."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lender_wallet":    {"type": "string", "description": "Lender hospital's Ethereum wallet address"},
                    "equipment_id":     {"type": "integer", "description": "On-chain equipment ID"},
                    "quantity":         {"type": "integer"},
                    "duration_hours":   {"type": "integer"},
                    "borrower_wallet":  {"type": "string", "description": "Borrower hospital's Ethereum wallet address"}
                },
                "required": ["lender_wallet", "equipment_id", "quantity", "duration_hours", "borrower_wallet"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_delivery_blockchain",
            "description": "Confirm delivery on-chain (REQUESTED → ACTIVE). Call after physical delivery.",
            "parameters": {
                "type": "object",
                "properties": {
                    "loan_id":         {"type": "integer"},
                    "confirmer_wallet": {"type": "string"}
                },
                "required": ["loan_id", "confirmer_wallet"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "settle_loan_blockchain",
            "description": "Settle loan on-chain (RETURN_PENDING → COMPLETED). Releases escrow funds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "loan_id": {"type": "integer"}
                },
                "required": ["loan_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_loan_status_blockchain",
            "description": "Get the current status of a loan from the smart contract.",
            "parameters": {
                "type": "object",
                "properties": {
                    "loan_id": {"type": "integer"}
                },
                "required": ["loan_id"]
            }
        }
    }
]


# ─────────────────────────────────────────────
# TOOL EXECUTOR
# ─────────────────────────────────────────────

def execute_tool(name: str, args: dict, hospital_id: str = None) -> dict:

    # ── Inventory / Backend ──────────────────────────────────────────────
    if name == "search_inventory":
        return safe_request("GET", "http://localhost:8000/inventory/search", params=args)

    if name == "get_hospitals":
        return safe_request("GET", "http://localhost:8000/hospitals")

    if name == "get_inventory":
        return safe_request("GET", f"http://localhost:8000/inventory/{args['hospital_id']}")

    # ── GIS ──────────────────────────────────────────────────────────────
    if name == "find_nearest_hospitals":
        hospitals = safe_request("GET", "http://localhost:8000/hospitals")
        if "error" in hospitals:
            return hospitals

        gis_input = [
            {"id": h["id"], "lat": h["location"]["lat"], "lon": h["location"]["lon"]}
            for h in hospitals
        ]
        return safe_request(
            "POST",
            "http://localhost:8001/gis/best-option",
            json={"origin": args, "hospitals": gis_input}
        )

    if name == "get_route":
        return safe_request("POST", "http://localhost:8001/gis/route", json=args)

    if name == "get_route_map_url":
        # Returns a URL — your GIS server renders the HTML map at /gis/route-map
        # We expose that URL to the frontend so it can open it in the map dialog
        params = (
            f"origin_lat={args['origin_lat']}&origin_lon={args['origin_lon']}"
            f"&dest_lat={args['dest_lat']}&dest_lon={args['dest_lon']}"
        )
        url = f"http://localhost:8001/gis/route-map?{params}"
        return {"map_url": url, "embed_url": url}

    if name == "get_isochrone":
        return safe_request("POST", "http://localhost:8001/gis/isochrone", json=args)

    # ── Dispatch ─────────────────────────────────────────────────────────
    if name == "dispatch":
        return safe_request("POST", "http://localhost:8000/dispatch", json=args)

    # ── Approval gate ────────────────────────────────────────────────────
    if name == "request_user_approval":
        # Store the pending approval payload so the API can return it
        # and the frontend can render the approval card + map dialog
        return {
            "approval_required": True,
            "loan_proposal": args,
            "message": (
                f"📋 **Loan Proposal Ready**\n"
                f"• Equipment: {args.get('quantity')}x {args.get('equipment_type')}\n"
                f"• From: {args.get('from_hospital_name')} ({args.get('from_hospital_id')})\n"
                f"• Duration: {args.get('duration_hours')} hours\n"
                f"• Distance: {args.get('distance_km', 'N/A')} km  |  ETA: {args.get('eta_min', 'N/A')} min\n\n"
                "**Please reply 'yes' / 'approve' to confirm, or 'no' / 'cancel' to abort.**"
            )
        }

    # ── Blockchain ───────────────────────────────────────────────────────
    if name == "create_blockchain_loan":
        return create_loan_on_chain(
            lender_wallet=args["lender_wallet"],
            equipment_id=args["equipment_id"],
            quantity=args["quantity"],
            duration_hours=args["duration_hours"],
            borrower_wallet=args["borrower_wallet"]
        )

    if name == "confirm_delivery_blockchain":
        return confirm_delivery_on_chain(args["loan_id"], args["confirmer_wallet"])

    if name == "settle_loan_blockchain":
        return settle_loan_on_chain(args["loan_id"])

    if name == "get_loan_status_blockchain":
        return get_loan_status(args["loan_id"])

    return {"error": f"Unknown tool: {name}"}


# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are Sanjeevani AI — a healthcare logistics orchestrator for a B2B hospital equipment-sharing platform backed by Ethereum smart contracts.

## Your capabilities
- search_inventory        → which hospitals have item X
- get_hospitals           → list all hospitals
- get_inventory           → full stock of one hospital
- find_nearest_hospitals  → rank by road distance/ETA
- get_route               → driving directions between two points
- get_route_map_url       → OSM interactive map URL (always fetch this for dispatch flows)
- get_isochrone           → reachable-area coverage
- dispatch                → backend inventory transfer record
- request_user_approval   → MANDATORY before any loan/dispatch — shows user the loan summary
- create_blockchain_loan  → locks funds in escrow on-chain (after approval only)
- confirm_delivery_blockchain → marks delivery active on-chain
- settle_loan_blockchain  → releases escrow after return
- get_loan_status_blockchain  → check loan state

## Workflow for "borrow / dispatch / loan" requests
1. search_inventory (hospital_id="all") to find hospitals with item
2. find_nearest_hospitals to rank them by distance from caller
3. Cross-reference: pick the nearest hospital that HAS the item
4. get_route_map_url to get the OSM map link
5. request_user_approval — ALWAYS call this, include map URL, distance, ETA
6. If user approves → dispatch (backend) + create_blockchain_loan (escrow)
7. Emit stage notifications at each step (see format below)

## Stage notification format
At the START of each tool call, prepend a short status line:
  🔍 Searching inventory across all hospitals...
  📍 Calculating nearest hospital with available stock...
  🗺️  Generating route map...
  📋 Preparing loan proposal for your approval...
  ⛓️  Recording loan on blockchain escrow...
  ✅ Loan created! Transaction hash: 0x...

## Rules
- NEVER create a loan without calling request_user_approval first
- NEVER guess inventory or hospital data — always use tools
- ALWAYS get route_map_url and include it in the approval proposal
- After blockchain loan creation, show the tx hash and loan ID prominently
- Keep responses concise — use markdown tables where helpful
- If user says "yes", "approve", "confirm", "sanction" → proceed with dispatch + blockchain
- If user says "no", "cancel", "abort" → cancel gracefully
- Remember conversation context — don't re-ask for info already given
"""


# ─────────────────────────────────────────────
# MAIN AGENT  (with persistent session memory)
# ─────────────────────────────────────────────

def run_agent(
    user_query: str,
    session_id: str,
    hospital_id: str = None,
    notify: Callable[[str], None] = None,  # SSE progress callback
) -> dict:
    """
    Returns:
      {
        "reply": str,           # assistant text
        "approval_required": bool,
        "loan_proposal": dict | None,
        "map_url": str | None,
        "tx_hash": str | None,
        "loan_id": int | None,
      }
    """

    def emit(msg: str):
        if notify:
            notify(msg)
        print(f"  📢 {msg}")

    # ── Inject caller location once per session ─────────────────────────
    messages = get_session(session_id)

    contextual_query = user_query
    if hospital_id:
        loc = get_hospital_location(hospital_id)
        if loc and not any("Caller location" in m.get("content", "") for m in messages):
            contextual_query += f" [Caller location: lat={loc['lat']}, lon={loc['lon']}]"

    messages.append({"role": "user", "content": contextual_query})

    # ── Response metadata collectors ───────────────────────────────────
    result_meta = {
        "reply": "",
        "approval_required": False,
        "loan_proposal": None,
        "map_url": None,
        "tx_hash": None,
        "loan_id": None,
    }

    MAX_ITERATIONS = 15

    for iteration in range(MAX_ITERATIONS):
        print(f"\n🔄  Agent iteration {iteration + 1}")

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=2048
        )

        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # ── Final text answer ────────────────────────────────────────────
        if finish_reason == "stop" or not msg.tool_calls:
            final = msg.content or "Operation completed."
            messages.append({"role": "assistant", "content": final})
            result_meta["reply"] = final
            return result_meta

        # ── Append assistant tool-call turn ─────────────────────────────
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        })

        # ── Execute each tool ────────────────────────────────────────────
        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name

            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}

            # Stage notification
            stage_labels = {
                "search_inventory":           "🔍 Searching inventory across all hospitals...",
                "get_hospitals":              "🏥 Fetching hospital registry...",
                "get_inventory":              "📦 Retrieving hospital inventory...",
                "find_nearest_hospitals":     "📍 Calculating nearest hospitals by road distance...",
                "get_route":                  "🛣️  Computing optimal route...",
                "get_route_map_url":          "🗺️  Generating interactive route map...",
                "get_isochrone":              "🔵 Computing reachable coverage area...",
                "dispatch":                   "🚚 Recording dispatch in backend...",
                "request_user_approval":      "📋 Preparing loan proposal for your review...",
                "create_blockchain_loan":     "⛓️  Creating loan on blockchain escrow...",
                "confirm_delivery_blockchain":"✅ Confirming delivery on-chain...",
                "settle_loan_blockchain":     "💰 Settling escrow and releasing funds...",
                "get_loan_status_blockchain": "🔎 Fetching loan status from chain...",
            }
            emit(stage_labels.get(tool_name, f"⚙️  Calling {tool_name}..."))

            print(f"\n🛠  TOOL: {tool_name}")
            print(f"    ARGS: {json.dumps(args, indent=2)}")

            tool_result = execute_tool(tool_name, args, hospital_id)

            print(f"    RESULT: {json.dumps(tool_result, indent=2)[:400]}")

            # ── Capture metadata from tool results ───────────────────────
            if tool_name == "get_route_map_url" and "map_url" in tool_result:
                result_meta["map_url"] = tool_result["map_url"]

            if tool_name == "request_user_approval":
                result_meta["approval_required"] = tool_result.get("approval_required", False)
                result_meta["loan_proposal"]     = tool_result.get("loan_proposal")
                if "route_map_url" in (tool_result.get("loan_proposal") or {}):
                    result_meta["map_url"] = tool_result["loan_proposal"]["route_map_url"]

            if tool_name == "create_blockchain_loan":
                result_meta["tx_hash"] = tool_result.get("tx_hash")
                result_meta["loan_id"] = tool_result.get("loan_id")

            # ── Append tool result to history ────────────────────────────
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })

            # ── Hard stop: approval required — return immediately ────────
            # Let the frontend show the approval card; next user message
            # ("yes/no") will continue the same session.
            if tool_name == "request_user_approval" and tool_result.get("approval_required"):
                result_meta["reply"] = tool_result["message"]
                # Append as assistant message so memory is preserved
                messages.append({"role": "assistant", "content": tool_result["message"]})
                return result_meta

    result_meta["reply"] = "⚠️ Reached maximum steps. Please try a more specific query."
    return result_meta