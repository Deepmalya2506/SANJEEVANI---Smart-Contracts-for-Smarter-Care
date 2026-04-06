import os
import json
from groq import Groq
from dotenv import load_dotenv

from mcp_server.main import search_inventory, get_best_option, create_loan

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama3-70b-8192"  # 🔥 best stable Groq model

# =========================
# TOOL DEFINITIONS
# =========================
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_inventory",
            "description": "Find hospitals with available equipment",
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
            "name": "get_best_option",
            "description": "Find nearest hospital from a list",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "object"},
                    "hospitals": {"type": "array"}
                },
                "required": ["origin", "hospitals"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_loan",
            "description": "Create blockchain loan request",
            "parameters": {
                "type": "object",
                "properties": {
                    "lender": {"type": "string"},
                    "equipment_id": {"type": "integer"},
                    "quantity": {"type": "integer"},
                    "duration": {"type": "integer"},
                    "value": {"type": "integer"}
                },
                "required": ["lender", "equipment_id", "quantity", "duration", "value"]
            }
        }
    }
]

# =========================
# TOOL EXECUTION MAP
# =========================
def execute_tool(name, args):
    if name == "search_inventory":
        return search_inventory(**args)

    elif name == "get_best_option":
        return get_best_option(**args)

    elif name == "create_loan":
        return create_loan(**args)

    return {"error": "Unknown tool"}

# =========================
# MAIN AGENT LOOP
# =========================
def run_agent(user_query):

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI healthcare logistics assistant. "
                "You must decide which tools to call to fulfill the request. "
                "Workflow: inventory → GIS → blockchain."
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

        # 🧠 If no tool → final answer
        if not msg.tool_calls:
            return msg.content

        # 🔧 Execute tool
        tool_call = msg.tool_calls[0]
        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"\n🛠 TOOL CALLED: {tool_name}")
        print("ARGS:", args)

        result = execute_tool(tool_name, args)

        print("RESULT:", result)

        # 🔁 Feed back to LLM
        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })