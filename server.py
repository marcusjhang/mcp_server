import os
import pandas as pd
from fastmcp import FastMCP
from openai import OpenAI

DATA_PATH = os.path.join(os.path.dirname(__file__), "dummy_data")

# Load OpenAI key once
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

mcp = FastMCP("BookOps Server")

@mcp.tool()
def explain_pnl(book_id: str, date: str) -> dict:
    """Explain the PnL for a given book and date, using LLM for explanation."""
    trades = pd.read_csv(os.path.join(DATA_PATH, "trades.csv"))
    trades = trades[(trades['book_id'] == book_id) & (trades['date'] == date)]
    if trades.empty:
        summary = f"No trades found for book {book_id} on {date}."
        return {"book_id": book_id, "date": date, "pnl": 0, "summary": summary}

    pnl = trades.apply(lambda r: r['qty'] * r['price'] * (1 if r['side'] == 'SELL' else -1), axis=1).sum()
    prompt = (
        f"The trading book {book_id} had a net P&L of ${pnl:,.2f} on {date}. "
        "Summarize this result in plain English for a portfolio manager."
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert hedge fund operations analyst."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
        temperature=0.3,
    )
    llm_summary = response.choices[0].message.content.strip()
    return {
        "book_id": book_id,
        "date": date,
        "pnl": pnl,
        "summary": llm_summary
    }

@mcp.tool()
def audit_exposure(book_id: str) -> dict:
    """List top exposures for a trading book, with LLM-written summary."""
    positions = pd.read_csv(os.path.join(DATA_PATH, "positions.csv"))
    book_positions = positions[positions['book_id'] == book_id]
    if book_positions.empty:
        return {"book_id": book_id, "top_exposures": [], "summary": "No positions found."}
    sector_exposure = book_positions.groupby('sector')['qty'].sum()
    total_qty = sector_exposure.sum()
    top = [{"sector": s, "exposure": float(q) / total_qty} for s, q in sector_exposure.items()]
    top.sort(key=lambda x: x['exposure'], reverse=True)
    top2 = top[:2]
    exposure_str = ', '.join([f"{t['sector']} ({t['exposure']*100:.1f}%)" for t in top2])
    prompt = (
        f"For book {book_id}, the top sector exposures are: {exposure_str}. "
        "Summarize these exposures and provide any relevant comments."
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a financial risk analyst."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=120,
        temperature=0.3,
    )
    llm_summary = response.choices[0].message.content.strip()
    return {"book_id": book_id, "top_exposures": top2, "summary": llm_summary}

if __name__ == "__main__":
    mcp.run(transport="stdio")