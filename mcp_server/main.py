import os
import json
from groq import Groq
from dotenv import load_dotenv

from app.services.gis_client import get_best_option
from app.services.blockchain_client import create_loan
from app.core.database import inventory_collection, hospital_collection

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"

# =========================
# TOOL FUNCTIONS
# =========================

def search_inventory(equipment_type: int, quantity: int):
    results = list(inventory_collection.aggregate([
        {"$match": {"equipment_type": equipment_type, "status": "AVAILABLE"}},
        {"$group": {"_id": "$hospital_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": quantity}}}
    ]))

    hospital_ids = [r["_id"] for r in results]

    hospitals = list(hospital_collection.find(
        {"id": {"$in": hospital_ids}},
        {"_id": 0}
    ))

    return hospitals


def get_location_of_hospitals(hospitals):
    return [
        {
            "id": h["id"],
            "lat": h["location"]["lat"],
            "lon": h["location"]["lon"]
        }
        for h in hospitals
    ]

def get_hospital_location(hospital_id):
    hospital = hospital_collection.find_one({"id": hospital_id})
    if not hospital:
        return None
    return hospital["location"]

# =========================
# TOOL DEFINITIONS (LLM)
# =========================

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_inventory",
            "description": "Find hospitals with required equipment",
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
            "name": "dispatch",
            "description": "Select best hospital and create loan",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_type": {"type": "integer"},
                    "quantity": {"type": "integer"},
                    "lat": {"type": "number"},
                    "lon": {"type": "number"}
                },
                "required": ["equipment_type", "quantity", "lat", "lon"]
            }
        }
    }
]


# =========================
# TOOL EXECUTION
# =========================

def execute_tool(name, args):

    if name == "search_inventory":
        return search_inventory(**args)

    elif name == "dispatch":

        equipment_type = args["equipment_type"]
        quantity = args["quantity"]
        origin = {"lat": args["lat"], "lon": args["lon"]}

        # 1. inventory
        hospitals = search_inventory(equipment_type, quantity)

        if not hospitals:
            return {"error": "No hospitals available"}

        # 2. GIS
        gis_input = get_location_of_hospitals(hospitals)
        best = get_best_option(origin, gis_input)

        best_id = best["data"]["best_hospital"]

        selected = next(h for h in hospitals if h["id"] == best_id)

        # 3. blockchain
        loan = create_loan({
            "lender": selected["wallet"],
            "equipment_id": equipment_type,
            "quantity": quantity,
            "duration": 4,
            "value": 8000
        })

        return {
            "hospital": selected,
            "route": best,
            "loan": loan
        }

    return {"error": "Unknown tool"}


# =========================
# AGENT LOOP
# =========================

def run_agent(user_query: str, hospital_id: str = None):

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI healthcare logistics assistant.\n"
                f"The current hospital is: {hospital_id}.\n"
                "Use this as reference when answering.\n"
                "For queries like 'near me', use hospital location.\n"
            )
        },
        {"role": "user", "content": user_query}
    ]

    while True:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        if "near me" in user_query.lower() and hospital_id:
            location = get_hospital_location(hospital_id)
            if location:
                user_query += f" (location: {location})"

        tool_call = msg.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"\n🛠 TOOL: {name}")
        print("ARGS:", args)

        result = execute_tool(name, args)

        print("RESULT:", result)

        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })