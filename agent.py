import os
import openai
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # loads env variables
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
MCP_SERVER_URL = "http://localhost:8000/rpc"  # adjust if needed

# List the available tools for the LLM (aligns with MCP endpoints)
FUNCTIONS = [
  {
    "name": "explain_pnl",
    "description": "Explain the PnL for a given book and date.",
    "parameters": {
      "type": "object",
      "properties": {
        "book_id": {"type": "string", "description": "Trading book ID"},
        "date": {"type": "string", "description": "Date in YYYY-MM-DD"}
      },
      "required": ["book_id", "date"]
    }
  },
  {
    "name": "audit_exposure",
    "description": "List top exposures for a trading book.",
    "parameters": {
      "type": "object",
      "properties": {
        "book_id": {"type": "string", "description": "Trading book ID"}
      },
      "required": ["book_id"]
    }
  }
]

def call_mcp(function_name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "method": function_name,
        "params": arguments,
        "id": 1
    }
    r = requests.post(MCP_SERVER_URL, json=payload)
    r.raise_for_status()
    return r.json()["result"]

def agent_route(user_query):
    messages = [
        {"role": "system", "content": "You are a hedge fund operations agent. Pick the most relevant tool and supply the required arguments, using only the tools/functions listed."},
        {"role": "user", "content": user_query}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        functions=FUNCTIONS,
        function_call="auto"
    )
    fc = response.choices[0].message.function_call
    func_name, func_args = fc.name, json.loads(fc.arguments)
    print(f"LLM chose {func_name} with {func_args}")
    return call_mcp(func_name, func_args)

if __name__ == "__main__":
    print("Sample BookOps LLM Agent")
    print("Type queries like: 'Explain the PnL for book HF123 on 2024-06-01' or 'What are the main exposures for HF123?'")
    while True:
        user_query = input("> ")
        output = agent_route(user_query)
        print(output)