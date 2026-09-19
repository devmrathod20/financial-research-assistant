
import os
import yfinance as yf
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_tavily import TavilySearch

load_dotenv()

# -----------------------------------------------------------
# 1. Deterministic Data & Calculation Tools
# -----------------------------------------------------------
class FinancialStatementInput(BaseModel):
    ticker: str = Field(description="Stock ticker symbol, e.g. NVDA, AAPL, MSFT")

@tool("get_quarterly_financials", args_schema=FinancialStatementInput)
def get_quarterly_financials(ticker: str) -> str:
    """Fetches exact, audited quarterly income statement figures from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker.upper())
        financials = stock.quarterly_income_stmt
        if financials is None or financials.empty:
            return f"No quarterly financial records found for {ticker}."
        
        recent = financials.iloc[:, :2]
        lines = [f"Audited Financial Results for {ticker.upper()}:"]
        for col in recent.columns:
            date_str = col.strftime("%Y-%m-%d")
            rev = recent.loc["Total Revenue", col] if "Total Revenue" in recent.index else 0
            net_inc = recent.loc["Net Income", col] if "Net Income" in recent.index else 0
            op_inc = recent.loc["Operating Income", col] if "Operating Income" in recent.index else 0
            
            lines.append(
                f"\n--- Quarter Ended {date_str} ---\n"
                f"• Total Revenue: ${rev:,.0f}\n"
                f"• Operating Income: ${op_inc:,.0f}\n"
                f"• Net Income: ${net_inc:,.0f}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving financials for {ticker}: {str(e)}"

class CompoundGrowthInput(BaseModel):
    initial_amount: float = Field(description="Starting investment amount")
    annual_addition: float = Field(description="Annual amount contributed")
    rate_percent: float = Field(description="Expected annual rate of return in percent (e.g. 12)")
    years: int = Field(description="Total investment horizon in years")

@tool("compound_growth_calculator", args_schema=CompoundGrowthInput)
def compound_growth_calculator(initial_amount: float, annual_addition: float, rate_percent: float, years: int) -> str:
    """Calculates future investment balance and total interest earned."""
    r = float(rate_percent) / 100.0
    total = float(initial_amount)
    contributions = float(initial_amount)
    
    for _ in range(int(years)):
        total = (total + float(annual_addition)) * (1.0 + r)
        contributions += float(annual_addition)
        
    interest_earned = total - contributions
    return (
        f"Initial: ${initial_amount:,.2f} | "
        f"Total Contributions: ${contributions:,.2f} | "
        f"Projected Balance: ${total:,.2f} | "
        f"Total Gain: ${interest_earned:,.2f}"
    )

class ExportReportInput(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    content: str = Field(description="Report markdown text")

@tool("export_financial_report", args_schema=ExportReportInput)
def export_financial_report(ticker: str, content: str) -> str:
    """Saves the financial brief into a local markdown file."""
    filename = f"{ticker.upper()}_research_brief.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Financial Analysis: {ticker.upper()}\n\n{content}\n")
    return f"Report successfully saved to {filename}"

# Qualitative news search
tavily_tool = TavilySearch(max_results=2, topic="finance")
tools = [get_quarterly_financials, tavily_tool, compound_growth_calculator, export_financial_report]

# -----------------------------------------------------------
# 2. Agent Factory
# -----------------------------------------------------------
def build_agent():
    llm = init_chat_model(
        model="openai/gpt-oss-120b",
        model_provider="groq",
        temperature=0.0
    )
    
    checkpointer = InMemorySaver()
    summarizer = SummarizationMiddleware(
        model=llm,
        trigger=("messages", 10),
        keep=("messages", 4)
    )
    
    return create_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        middleware=[summarizer],
        system_prompt=(
            "You are an expert Wall Street financial analyst.\n"
            "RULES:\n"
            "1. When reporting numerical earnings, use 'get_quarterly_financials' to fetch audited SEC figures.\n"
            "2. Use 'tavily_search' only for qualitative catalysts and recent business developments.\n"
            "3. Use 'compound_growth_calculator' for investment scenario math.\n"
            "4. NEVER invent tools like open_file. Synthesize your responses cleanly."
        )
    )

agent = build_agent()

# -----------------------------------------------------------
# 3. Invocation Runner
# -----------------------------------------------------------
def ask_assistant(query: str, thread_id: str = "streamlit_session", max_steps: int = 5) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    state = agent.invoke({"messages": [HumanMessage(content=query)]}, config=config)
    
    steps = 0
    while steps < max_steps:
        last_msg = state["messages"][-1]
        if isinstance(last_msg, AIMessage) and getattr(last_msg, "tool_calls", None) and not last_msg.content:
            state = agent.invoke(None, config=config)
            steps += 1
        else:
            break
            
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
            
    return "Unable to produce a response."