import os
import streamlit as st
from src.assistant import ask_assistant

st.set_page_config(
    page_title="AlphaTerminal | AI Financial Research",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------
# Custom CSS: Glassmorphism, Clean Badges & Financial Chat Bubbles
# -----------------------------------------------------------
st.markdown("""
<style>
    /* Global typography & smooth scroll */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Top Header Styling */
    .terminal-header {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(14, 165, 233, 0.05) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
    }
    .terminal-title {
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .badge {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        background: rgba(16, 185, 129, 0.18);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 3px 10px;
        border-radius: 999px;
        letter-spacing: 0.5px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0E1524;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    /* Chat message containers */
    div[data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
    }
    
    /* Differentiate User vs Assistant messages */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #131D2E;
        border: 1px solid rgba(16, 185, 129, 0.18);
    }

    /* Markdown Tables inside answers */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 14px 0;
        font-size: 13.5px;
    }
    th {
        background: rgba(255, 255, 255, 0.06);
        color: #10B981;
        text-align: left;
        padding: 10px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    td {
        padding: 9px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    tr:hover {
        background: rgba(255, 255, 255, 0.02);
    }

    /* Floating input bar polish */
    div[data-testid="stChatInput"] {
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Sidebar: System Stats & Quick Actions
# -----------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎛️ Terminal Engine")
    st.markdown(
        """
        **Status:** `🟢 Connected`  
        **Model:** `Groq / Llama 3.1 8B Instant`  
        **Data Grounding:** `Yahoo Finance SEC 10-Q`  
        **Search:** `Tavily Finance Topic`  
        **State:** `In-Memory Checkpointer`  
        """
    )
    st.divider()

    st.markdown("### ⚡ Quick Research Tickers")
    col1, col2, col3 = st.columns(3)
    quick_query = None
    if col1.button("NVDA", use_container_width=True):
        quick_query = "What are the latest audited revenue and net income figures for NVIDIA (NVDA)?"
    if col2.button("AAPL", use_container_width=True):
        quick_query = "What are the latest audited revenue and net income figures for Apple (AAPL)?"
    if col3.button("MSFT", use_container_width=True):
        quick_query = "What are the latest audited revenue and net income figures for Microsoft (MSFT)?"

    st.divider()
    st.markdown("### 📁 Exported Research Briefs")
    report_file = "NVDA_research_brief.md"
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            brief_content = f.read()
        st.download_button(
            label="⬇️ Download Latest Brief (.md)",
            data=brief_content,
            file_name=report_file,
            mime="text/markdown",
            use_container_width=True
        )
        st.caption(f"Cached file: `{report_file}`")
    else:
        st.info("Ask the agent to export a report to generate a download file.")

    st.divider()
    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# -----------------------------------------------------------
# Main View Header Banner
# -----------------------------------------------------------
st.markdown(
    """
    <div class="terminal-header">
        <div class="terminal-title">
            <span>📈 AlphaTerminal</span>
            <span class="badge">SEC-Grounded Intelligence</span>
        </div>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 14px;">
            Autonomous Wall Street analyst engine synthesizing SEC-audited filings, market news catalysts, and deterministic investment modeling.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------
# Conversation State
# -----------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Render chat history with icons
for msg in st.session_state.chat_history:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Process input (either from chat bar or quick ticker buttons)
user_prompt = st.chat_input("Query audited earnings, growth scenarios, or catalysts...")
active_prompt = quick_query or user_prompt

if active_prompt:
    st.session_state.chat_history.append({"role": "user", "content": active_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(active_prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Fetching audited filings & computing projections..."):
            response = ask_assistant(active_prompt, thread_id="styled_session")
            st.markdown(response)

    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.rerun()