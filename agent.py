import os
import openai
import json
import subprocess
import time
import json
import subprocess
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# No MCP_SERVER_URL needed for stdio

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

def call_mcp_stdio(function_name, arguments):
    init = {
        "jsonrpc":"2.0","id":1,
        "method":"initialize",
        "params":{
            "protocolVersion":"2025-03-26",
            "capabilities":{},
            "clientInfo":{"name":"BookOpsAgent","version":"0.1"}
        }
    }
    initialized_notify = {"jsonrpc":"2.0","method":"notifications/initialized"}
    call = {
        "jsonrpc":"2.0","id":2,
        "method":"tools/call",
        "params":{"name":function_name,"arguments":arguments}
    }

    payload = "\n".join([
        json.dumps(init),
        json.dumps(initialized_notify),
        json.dumps(call),
        ""
    ])

    proc = subprocess.Popen(
        ["python", "server.py"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    out, err = proc.communicate(payload)

    if err:
        print("Error from MCP server:", err)

    lines = [line for line in out.splitlines() if line.startswith("{")]
    for line in lines:
        resp = json.loads(line)
        if resp.get("id") == 2:
            if "result" in resp:
                return resp["result"]
            raise Exception("Tool call error: " + str(resp))

    raise Exception("No valid response, raw output:\n" + out)

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
    return call_mcp_stdio(func_name, func_args)

if __name__ == "__main__":
    print("Sample BookOps LLM Agent (STDIO)")
    print("Type queries like: 'Explain the PnL for book HF123 on 2024-06-01' or 'What are the main exposures for HF123?'")
    while True:
        user_query = input("> ")
        output = agent_route(user_query)
        print(output)