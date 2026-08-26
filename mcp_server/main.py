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
import re
import requests
from groq import Groq
from dotenv import load_dotenv
import os
from typing import Optional, Callable

from app.core.database import hospital_collection
from mcp_server.blockchain_tools import (
    register_equipment_on_chain,
    create_loan_on_chain,
    confirm_delivery_on_chain,
    settle_loan_on_chain,
    get_loan_status,
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=60.0)

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
_pending_approval_collection = hospital_collection.database["pending_approvals"]


def save_pending_approval(session_id: str, approval: dict) -> None:
    _pending_approvals[session_id] = approval
    _pending_approval_collection.replace_one(
        {"session_id": session_id},
        {"session_id": session_id, "approval": approval},
        upsert=True,
    )


def take_pending_approval(session_id: str) -> dict | None:
    approval = _pending_approvals.pop(session_id, None)
    if approval is None:
        stored = _pending_approval_collection.find_one_and_delete({"session_id": session_id})
        approval = stored.get("approval") if stored else None
    else:
        _pending_approval_collection.delete_one({"session_id": session_id})
    return approval


def discard_pending_approval(session_id: str) -> None:
    _pending_approvals.pop(session_id, None)
    _pending_approval_collection.delete_one({"session_id": session_id})


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
    
def get_hospital_by_id(hospital_id: str):
    for hospital in hospital_collection.find({"id": hospital_id}):
        wallet = hospital.get("wallet", "")
        if isinstance(wallet, str) and len(wallet) == 42 and wallet.startswith("0x"):
            try:
                int(wallet[2:], 16)
                return hospital
            except ValueError:
                continue
    return None


# ─────────────────────────────────────────────
# TOOL DEFINITIONS
# ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_inventory",
            "description": ( "Search hospitals for a specific equipment type and minimum quantity. " "Pass hospital_id='all' to search across ALL hospitals. " "Returns list of hospitals that have the item available." ),
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_type": {"type": "integer"},
                    "quantity": {"type": "integer"}
                },
                "required": ["equipment_type", "quantity"]
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
                    "duration_hours":     {"type": "number"},
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
            "name": "register_equipment_blockchain",
            "description": "Register one equipment type on the smart contract. Amounts are in wei; the contract assigns the next equipment ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "hourly_rate_wei": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
                    "caution_deposit_wei": {"anyOf": [{"type": "integer"}, {"type": "string"}]}
                },
                "required": ["name", "hourly_rate_wei", "caution_deposit_wei"]
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
    },
    {
        "type": "function",
        "function": {
            "name": "upload_inventory_csv",
            "description": "Upload a CSV file to populate hospital inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        }
    }
]


# ─────────────────────────────────────────────
# TOOL EXECUTOR
# ─────────────────────────────────────────────

def execute_tool(name: str, args: dict, hospital_id: str = None, session_id: str = None) -> dict:

    # ── Inventory / Backend ──────────────────────────────────────────────

    if name == "upload_inventory_csv":
        files = {"file": open(args["file_path"], "rb")}

        return safe_request(
            "POST",
            "http://localhost:8000/inventory/upload",
            files=files
        )

    if name == "search_inventory":
        return safe_request(
            "GET",
            "http://localhost:8000/inventory/search",
            params={
                "equipment_type": int(args["equipment_type"]),
                "quantity": args["quantity"]
            }
        )

    if name == "get_hospitals":
        hospitals = safe_request("GET", "http://localhost:8000/hospitals")
        if isinstance(hospitals, dict) and isinstance(hospitals.get("value"), list):
            hospitals = hospitals["value"]
        if not isinstance(hospitals, list):
            return {"error": "Backend returned an invalid hospital list"}

        valid_hospitals = []
        seen_ids = set()
        for hospital in hospitals:
            hospital_id_value = hospital.get("id") if isinstance(hospital, dict) else None
            location = hospital.get("location") if isinstance(hospital, dict) else None
            if (
                not hospital_id_value
                or hospital_id_value in seen_ids
                or not isinstance(location, dict)
                or not isinstance(location.get("lat"), (int, float))
                or not isinstance(location.get("lon"), (int, float))
            ):
                continue
            seen_ids.add(hospital_id_value)
            valid_hospitals.append(hospital)
        return valid_hospitals

    if name == "get_inventory":
        return safe_request("GET", f"http://localhost:8000/inventory/{args['hospital_id']}")

    # ── GIS ──────────────────────────────────────────────────────────────
    if name == "find_nearest_hospitals":
        hospitals = safe_request("GET", "http://localhost:8000/hospitals")

        if "error" in hospitals:
            return hospitals

        if isinstance(hospitals, dict) and isinstance(hospitals.get("value"), list):
            hospitals = hospitals["value"]
        if not isinstance(hospitals, list):
            return {"error": "Backend returned an invalid hospital list"}

        gis_input = []
        seen_ids = set()
        for hospital in hospitals:
            location = hospital.get("location") if isinstance(hospital, dict) else None
            hospital_id_value = hospital.get("id") if isinstance(hospital, dict) else None
            if (
                not hospital_id_value
                or hospital_id_value in seen_ids
                or not isinstance(location, dict)
                or not isinstance(location.get("lat"), (int, float))
                or not isinstance(location.get("lon"), (int, float))
            ):
                continue
            seen_ids.add(hospital_id_value)
            gis_input.append({
                "id": hospital_id_value,
                "lat": location["lat"],
                "lon": location["lon"],
            })

        if not gis_input:
            return {"error": "No valid hospitals with coordinates were found"}

        res = safe_request(
            "POST",
            "http://localhost:8001/gis/best-option",
            json={
                "origin": args,
                "hospitals": gis_input
            }
        )

        return res.get("data", res)   # 🔥 CRITICAL FIX

    if name == "get_route":
        return safe_request(
            "POST",
            "http://localhost:8001/gis/route",
            json={
                "source": args["origin"],   # 🔥 FIX
                "destination": args["destination"]
            }
        )

    if name == "get_route_map_url":
        res = safe_request(
            "POST",
            "http://localhost:8001/gis/route-map",
            json={
                "source": {
                    "lat": args["origin_lat"],
                    "lon": args["origin_lon"]
                },
                "destination": {
                    "lat": args["dest_lat"],
                    "lon": args["dest_lon"]
                }
            }
        )

        if "map_file" in res:
            res["map_url"] = f"http://localhost:8001/{res['map_file']}"  # 🔥 FIX

        return res

    if name == "get_isochrone":
        return safe_request("POST", "http://localhost:8001/gis/isochrone", json=args)

    # ── Dispatch ─────────────────────────────────────────────────────────
    if name == "dispatch":
        equipment_types = {"oxygen-cylinder": 1, "oxygen cylinder": 1, "ventilator": 2}
        normalized_args = {
            **args,
            "equipment_type": equipment_types.get(
                str(args.get("equipment_type", "")).lower(),
                args.get("equipment_type", 1),
            ),
        }
        return safe_request("POST", "http://localhost:8000/dispatch", json=normalized_args)

    # ── Approval gate ────────────────────────────────────────────────────
    if name == "request_user_approval":
        save_pending_approval(session_id, args)

        return {
            "approval_required": True,
            "loan_proposal": args,
            "message": "Awaiting approval..."
        }
    
    # ── Blockchain ───────────────────────────────────────────────────────
    if name == "register_equipment_blockchain":
        return register_equipment_on_chain(
            name=args["name"],
            hourly_rate_wei=int(str(args["hourly_rate_wei"]), 0),
            caution_deposit_wei=int(str(args["caution_deposit_wei"]), 0),
        )

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

### Equipment-mapping:
equipment | equipment_type
Oxygen-Cylinder: 1
Ventilator: 2

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
- register_equipment_blockchain → registers one equipment type and returns its assigned ID
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
 Tool arguments must be valid JSON. Use literal numeric values only; never write arithmetic expressions such as `distance/60` or `34.6/1` in arguments.
- NEVER create a loan without calling request_user_approval first
- For equipment registration, call register_equipment_blockchain directly. Do not redirect to CSV inventory upload.
- ALWAYS get route_map_url and include it in the approval proposal
- If the user gives a location but no hospital_id, use the first registered hospital as the receiving hospital; do not ask the user for an ID.
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
    notify: Callable[[str], None] = None) -> dict:

    
    # 🔥 APPROVAL HANDLING
    pending_approval = _pending_approval_collection.find_one({"session_id": session_id})
    if session_id in _pending_approvals or pending_approval:
        if user_query.lower() in ["no", "cancel", "abort"]:
            discard_pending_approval(session_id)
            return {"reply": "Loan request cancelled."}
        if user_query.lower() in ["yes", "approve", "confirm"]:
            approval = take_pending_approval(session_id)
            if approval is None:
                return {"reply": "This approval has expired. Please submit the loan request again."}

            from_hospital = get_hospital_by_id(approval["from_hospital_id"])
            destination_id = approval.get("to_hospital_id") or hospital_id
            to_hospital = get_hospital_by_id(destination_id) if destination_id else None
            if to_hospital is None:
                hospitals = list(hospital_collection.find({}, {"_id": 0}).limit(1))
                to_hospital = hospitals[0] if hospitals else None

            if from_hospital is None or to_hospital is None:
                return {"reply": "I could not identify the lending and receiving hospitals."}

            equipment_ids = {"oxygen-cylinder": 1, "oxygen cylinder": 1, "ventilator": 2}
            equipment_id = equipment_ids.get(str(approval.get("equipment_type", "")).lower(), 1)

            dispatch_result = execute_tool("dispatch", {
                "equipment_type": equipment_id,
                "quantity": approval["quantity"],
                "from_hospital_id": from_hospital["id"],
                "to_hospital_id": to_hospital["id"],
                "location": to_hospital.get("location", {"lat": 0, "lon": 0}),
                "skip_blockchain": True,
            }, hospital_id, session_id)

            if isinstance(dispatch_result, dict) and dispatch_result.get("error"):
                return {"reply": "Dispatch failed", "error": dispatch_result["error"]}

            loan_result = execute_tool("create_blockchain_loan", {
                "lender_wallet": from_hospital["wallet"],   # ✅ FIXED
                "equipment_id": equipment_id,
                "quantity": approval["quantity"],
                "duration_hours": approval["duration_hours"],
                "borrower_wallet": to_hospital["wallet"]    # ✅ FIXED
            }, hospital_id, session_id)

            if "error" in loan_result:
                return {"reply": "Blockchain loan failed", "error": loan_result["error"]}

            return {
                "reply": "✅ Loan approved and created successfully",
                "tx_hash": loan_result.get("tx_hash"),
                "loan_id": loan_result.get("loan_id")
            }
  

    def emit(msg: str):
        if notify:
            notify(msg)
        print(f"  📢 {msg}")

    # ── Resolve a receiving hospital for location-only requests ──────────
    if not hospital_id:
        default_hospital = hospital_collection.find_one({}, {"_id": 0, "id": 1})
        hospital_id = default_hospital.get("id") if default_hospital else None

    # ── Inject caller location once per session ─────────────────────────
    messages = get_session(session_id)[-10:]

    contextual_query = user_query
    coordinate_match = re.search(
        r"\(?\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*\)?",
        user_query,
    )
    if coordinate_match:
        requested_lat, requested_lon = coordinate_match.groups()
        contextual_query += (
            f" [AUTHORITATIVE requested location: lat={requested_lat}, "
            f"lon={requested_lon}; use these exact coordinates]"
        )
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
            max_tokens=4096
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

                # 🔥 FIX: enforce correct schema BEFORE tool execution
                if tool_call.function.name == "request_user_approval":

                    if "duration_hours" in args:
                        # convert float → int, minimum 1 hour
                        args["duration_hours"] = max(1, int(round(args["duration_hours"])))

                    if "eta_min" in args:
                        args["eta_min"] = int(round(args["eta_min"]))

                    if "distance_km" in args:
                        args["distance_km"] = round(args["distance_km"], 2)
                
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

            tool_result = execute_tool(tool_name, args, hospital_id, session_id)

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
            def compress_tool_output(tool_name, result):
                if isinstance(result, dict):

                    # 🔥 remove heavy geometry
                    if "geometry" in str(result):
                        result = {
                            "summary": "Route computed successfully"
                        }

                    # 🔥 trim GIS results
                    if "all_options" in result:
                        result["all_options"] = result["all_options"][:2]

                    # 🔥 trim hospitals
                    if isinstance(result, list) and len(result) > 3:
                        return result[:3]

                return result


            compressed_result = compress_tool_output(tool_name, tool_result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(compressed_result, default=str)
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