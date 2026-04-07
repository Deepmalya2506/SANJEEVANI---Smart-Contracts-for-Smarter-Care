import json
import requests
from groq import Groq
from dotenv import load_dotenv
import os

from app.core.database import hospital_collection

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# =========================
# HELPERS
# =========================

def get_hospital_location(hospital_id):
    hospital = hospital_collection.find_one({"id": hospital_id})
    return hospital["location"] if hospital else None

def safe_request(method, url, **kwargs):
    try:
        res = requests.request(method, url, timeout=10, **kwargs)

        print("\n🌐 CALL:", url)
        print("STATUS:", res.status_code)
        print("RAW:", res.text[:300])

        if res.status_code != 200:
            return {"error": f"{url} failed", "raw": res.text}

        try:
            return res.json()
        except:
            return {"error": "Invalid JSON", "raw": res.text}

    except Exception as e:
        return {"error": str(e)}
# =========================
# TOOL EXECUTOR
# =========================

def execute_tool(name, args, hospital_id=None):

    # ---------------- DB ----------------
    if name == "search_inventory":
        return safe_request(
            "GET",
            "http://localhost:8000/inventory/search",
            params=args
        )

    if name == "get_hospitals":
        return safe_request(
            "GET",
            "http://localhost:8000/hospitals"
        )

    if name == "get_inventory":
        return safe_request(
            "GET",
            f"http://localhost:8000/inventory/{args['hospital_id']}"
        )

    # ---------------- GIS ----------------
    if name == "find_nearest_hospitals":

        hospitals = safe_request(
            "GET",
            "http://localhost:8000/hospitals"
        )

        if "error" in hospitals:
            return hospitals

        gis_input = [
            {
                "id": h["id"],
                "lat": h["location"]["lat"],
                "lon": h["location"]["lon"]
            }
            for h in hospitals
        ]

        return safe_request(
            "POST",
            "http://localhost:8001/gis/best-option",
            json={
                "origin": args,
                "hospitals": gis_input
            }
        )

    if name == "get_route":
        return safe_request(
            "POST",
            "http://localhost:8001/gis/route",
            json=args
        )

    if name == "get_isochrone":
        return safe_request(
            "POST",
            "http://localhost:8001/gis/isochrone",
            json=args
        )

    # ---------------- DISPATCH ----------------
    if name == "dispatch":
        return safe_request(
            "POST",
            "http://localhost:8000/dispatch",
            json=args
        )

    return {"error": "Unknown tool"}

# =========================
# MCP AGENT
# =========================

def run_agent(user_query: str, hospital_id:str=None):

    # 🔥 inject context
    if hospital_id:
        loc = get_hospital_location(hospital_id)
        if loc:
            user_query += f" (location lat {loc['lat']} lon {loc['lon']})"

    messages = [
        {
            "role": "system",
            "content": (
                "You are Sanjeevani AI, a healthcare logistics orchestrator.\n\n"

                "You MUST decide which tool to use.\n\n"

                "Rules:\n"
                "- Equipment queries → search_inventory\n"
                "- Closest hospitals → find_nearest_hospitals\n"
                "- Route / distance → get_route\n"
                "- Coverage / radius → get_isochrone\n"
                "- Full request (send equipment) → dispatch\n"
                "- NEVER ask for location if provided\n"
                "- Always prefer tool usage over guessing\n"
            )
        },
        {"role": "user", "content": user_query}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_inventory",
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
                "name": "find_nearest_hospitals",
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
                "name": "dispatch",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "equipment_type": {"type": "integer"},
                        "quantity": {"type": "integer"},
                        "location": {"type": "object"}
                    },
                    "required": ["equipment_type", "quantity", "location"]
                }
            }
        }
    ]

    # 🔥 FIRST LLM CALL
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=tools
    )

    msg = response.choices[0].message

    # =========================
    # TOOL EXECUTION LOOP
    # =========================
    if msg.tool_calls:
        tool_call = msg.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        print(f"\n🛠 TOOL: {tool_call.function.name}")
        print("ARGS:", args)

        result = execute_tool(tool_call.function.name, args, hospital_id)

        print("RESULT:", result)

        # 🔁 RETURN TO LLM
    followup = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            *messages,
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": msg.tool_calls
            },
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            }
        ]
    )

    return followup.choices[0].message.content