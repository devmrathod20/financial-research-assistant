# 📈 Autonomous Financial Research Assistant

A production-style agentic assistant that synthesizes SEC-audited financial filings, qualitative market news, and deterministic compound interest modeling into comprehensive research briefs.

## Architecture Highlights
- **Deterministic Data Grounding:** Integrates `yfinance` directly into tool schemas to retrieve audited SEC 10-Q/10-K figures, eliminating hallucinations common with free-form web search aggregators.
- **Agent Orchestration:** Built on LangChain v1 & LangGraph (`create_agent`) with cyclical tool execution loops and input schema validation via Pydantic.
- **Short-Term Checkpointing:** Implements `InMemorySaver` for coreference resolution across conversational turns (e.g., tracking tickers implicitly).
- **Context Engineering:** Employs `SummarizationMiddleware` to compress dialogue turns once token boundaries are approached.
- **Fast Local Inference:** Powered by Groq's `llama-3.1-8b-instant` execution layer for low-latency multi-step tool calls.
- **Full UI:** Interactive dashboard built using Streamlit with markdown rendering and report downloads.

## Tech Stack
- **Frameworks:** LangChain, LangGraph, Streamlit
- **LLM Engine:** Groq (Meta Llama 3.1 8B Instant)
- **Tools:** Yahoo Finance API (`yfinance`), Tavily Search API
- **Package Manager:** `uv`

## Quickstart
1. Clone repo and install dependencies:
   ```bash
   uv sync