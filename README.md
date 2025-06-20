# 📘 BookOps MCP + LLM Project

This repository demonstrates a fast setup for:

1. **MCP Server** using FastMCP and stdout/stdin transport.
2. **LLM-powered Business Logic** within the MCP tool functions.
3. **Agent** that handles user input and orchestrates LLM function-calling + MCP tool invocation.

---

## 📁 File Structure

/
├── agent.py             # LLM agent that handles queries and calls MCP via subprocess
├── server.py            # FastMCP server defining tools explain_pnl & audit_exposure
├── dummy_data/
│   ├── trades.csv       # Contains book_id, date, symbol, qty, side, price
│   └── positions.csv    # Contains book_id, symbol, sector, qty
└── README.md            # This documentation

---

## 🛠️ Requirements

- Python 3.10+ (recommended version: 3.12)
- Install dependencies:
  ```bash
  pip install fastmcp openai pandas python-dotenv

	•	Ensure your .env includes:

OPENAI_API_KEY=sk-xxx



⸻

🚀 Running the System (STDIO Mode)

1. Start the MCP Server (in one terminal)

python server.py

This waits for client calls over stdin/stdout.

2. Run the Agent (in another terminal)

python agent.py

3. Example interaction:

> Explain the PnL for book HF123 on 2024-06-01
LLM chose explain_pnl …
{ "book_id": "HF123", "date": "...", "pnl": -72500.0, "summary": "…" }

4. Or ask:

> What are the main exposures for HF123?
LLM chose audit_exposure …
{ "book_id": "HF123", "top_exposures": [...], "summary": "..." }


⸻

🔄 How it Works
	1.	Agent uses LLM function-calling to choose a tool & arguments from FUNCTIONS.
	2.	Agent launches the server subprocess and sends MCP stdio JSON-RPC:
	•	initialize
	•	notifications/initialized
	•	tools/call
	3.	Server processes the request:
	•	Executes business Python & makes internal LLM calls.
	4.	Server returns JSON response.
	5.	Agent captures and displays it.