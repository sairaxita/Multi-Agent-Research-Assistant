"""
streamlit_app.py
Streamlit UI for the multi-agent research pipeline (pipeline.run_research_pipeline).

Run with:
    streamlit run streamlit_app.py

For the colors to fully apply (buttons, tabs, inputs), also drop the accompanying
config.toml into a ".streamlit" folder next to this file:
    your_project/
      streamlit_app.py
      .streamlit/
        config.toml
"""

import html as html_lib
import io
from contextlib import redirect_stdout

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pipeline import run_research_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_text(value) -> str:
    """Normalize whatever writer_chain/critic_chain return (str, AIMessage, dict) into plain text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    content = getattr(value, "content", None)
    if content is not None:
        return str(content)
    if isinstance(value, dict) and "content" in value:
        return str(value["content"])
    return str(value)


STAGES = [
    {"key": "step 1", "label": "Search", "emoji": "🔍", "color": "#38bdf8"},
    {"key": "step 2", "label": "Read", "emoji": "📖", "color": "#a855f7"},
    {"key": "step 3", "label": "Write", "emoji": "✍️", "color": "#fb923c"},
    {"key": "step 4", "label": "Critique", "emoji": "🧐", "color": "#f472b6"},
]


def stage_reached(log_text: str) -> int:
    """How many of pipeline.py's print() markers ('step 1'..'step 4') have shown up so far."""
    lower = log_text.lower()
    reached = 0
    for i, s in enumerate(STAGES):
        if s["key"] in lower:
            reached = i + 1
    return reached


def render_stage_tracker(placeholder, reached: int, all_done: bool = False):
    cards = []
    for i, s in enumerate(STAGES):
        idx = i + 1
        if all_done or idx < reached:
            state = "done"
        elif idx == reached:
            state = "active"
        else:
            state = "pending"
        cards.append(
            f'<div class="stage-card stage-{state}" '
            f'style="--stage-color:{s["color"]}; --stage-bg:{s["color"]}26;">'
            f'<div class="stage-emoji">{s["emoji"]}</div>'
            f'<div class="stage-label">{s["label"]}</div>'
            f"</div>"
        )
    placeholder.markdown(f'<div class="stage-row">{"".join(cards)}</div>', unsafe_allow_html=True)


class StreamlitLogStream(io.StringIO):
    """Redirects the pipeline's print() output into a live-updating terminal-style panel
    and drives the stage tracker off the same text, so the UI never just sits frozen."""

    def __init__(self, log_placeholder, stage_placeholder):
        super().__init__()
        self.log_placeholder = log_placeholder
        self.stage_placeholder = stage_placeholder
        self.text = ""

    def write(self, s):
        self.text += s
        safe = html_lib.escape(self.text) or " "
        self.log_placeholder.markdown(f'<div class="terminal">{safe}</div>', unsafe_allow_html=True)
        render_stage_tracker(self.stage_placeholder, stage_reached(self.text))
        return len(s)


# ---------------------------------------------------------------------------
# Page setup + styling
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Multi-Agent Research System", page_icon="🔎", layout="wide")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

.hero {
    background: linear-gradient(120deg, #7c3aed 0%, #ec4899 55%, #f59e0b 100%);
    padding: 1.8rem 2rem;
    border-radius: 20px;
    margin-bottom: 1.4rem;
    box-shadow: 0 10px 30px rgba(124,58,237,0.35);
}
.hero h1 {
    font-family: 'Space Grotesk', sans-serif;
    color: #ffffff !important;
    font-size: 2rem;
    margin: 0 0 4px 0;
}
.hero p { color: rgba(255,255,255,0.92); margin: 0; font-size: 1rem; }

.stage-row { display:flex; gap:10px; margin: 0.6rem 0 1.2rem 0; }
.stage-card {
    flex:1; text-align:center; padding: 16px 8px; border-radius:16px;
    border: 2px solid #2a2d3a; background:#171923; transition: all .35s ease;
}
.stage-pending { opacity:.35; }
.stage-active {
    border-color: var(--stage-color);
    animation: pulseGlow 1.3s ease-in-out infinite;
}
.stage-done {
    border-color: var(--stage-color);
    background: linear-gradient(160deg, var(--stage-bg), #171923);
}
.stage-emoji { font-size: 1.7rem; }
.stage-label { font-size:.82rem; font-weight:600; margin-top:6px; letter-spacing:.02em; }

@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 8px var(--stage-color); }
  50% { box-shadow: 0 0 26px var(--stage-color); }
}

.terminal {
    background:#05060a; color:#39ff88; font-family:'JetBrains Mono','Courier New',monospace;
    padding:14px 16px; border-radius:12px; max-height:280px; overflow-y:auto;
    border:1px solid #1f2430; font-size:.82rem; line-height:1.5;
    box-shadow: inset 0 0 25px rgba(57,255,136,0.08);
    white-space: pre-wrap;
}

div[data-testid="stButton"] button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: transform .15s ease, box-shadow .15s ease !important;
}
div[data-testid="stButton"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(139,92,246,0.45);
}

.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    border-bottom: 3px solid #ec4899 !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
        <h1> Multi-Agent Research System</h1>
        <p>Search agent → Reader agent → Writer chain → Critic chain, all in one run.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### ⚙️ About")
    st.write(
        "Runs the pipeline in `pipeline.py`: a search agent finds sources, a reader "
        "agent scrapes the best one, a writer drafts a report, and a critic reviews it."
    )
    st.caption("Make sure your `.env` (API keys) sits next to this script.")

# ---------------------------------------------------------------------------
# Input + run
# ---------------------------------------------------------------------------

topic = st.text_input("Research topic", placeholder="e.g. Latest advances in agentic RAG systems")
run_btn = st.button(" Run Research", type="primary", disabled=not topic.strip())

stage_placeholder = st.empty()
log_placeholder = st.empty()

# Re-render last known state on rerun (e.g. after switching tabs) instead of going blank
if "log_text" in st.session_state:
    render_stage_tracker(
        stage_placeholder,
        stage_reached(st.session_state["log_text"]),
        all_done="pipeline_state" in st.session_state,
    )
    log_placeholder.markdown(
        f'<div class="terminal">{html_lib.escape(st.session_state["log_text"])}</div>',
        unsafe_allow_html=True,
    )
else:
    render_stage_tracker(stage_placeholder, 0)

if run_btn:
    st.session_state.pop("pipeline_state", None)
    stream = StreamlitLogStream(log_placeholder, stage_placeholder)

    with st.status("Running pipeline...", expanded=True) as status:
        try:
            with redirect_stdout(stream):
                result = run_research_pipeline(topic)
            st.session_state["pipeline_state"] = result
            st.session_state["log_text"] = stream.text
            render_stage_tracker(stage_placeholder, len(STAGES), all_done=True)
            status.update(label="Pipeline complete", state="complete")
            st.balloons()
        except Exception as e:
            status.update(label="Pipeline failed", state="error")
            st.exception(e)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

if "pipeline_state" in st.session_state:
    state = st.session_state["pipeline_state"]
    report_text = to_text(state.get("report"))
    feedback_text = to_text(state.get("feedback"))

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Report", f"{len(report_text.split())} words")
    m2.metric("Feedback", f"{len(feedback_text.split())} words")
    m3.metric("Scraped content", f"{len(state.get('scraped_content', ''))} chars")

    tab_report, tab_feedback, tab_search, tab_scraped = st.tabs(
        ["Final Report", "Critic Feedback", "Search Results", "Scraped Content"]
    )

    with tab_report:
        with st.container(border=True):
            st.markdown(report_text or "_No report generated._")
            if report_text:
                st.download_button(
                    "Download report (.md)",
                    data=report_text,
                    file_name="research_report.md",
                    mime="text/markdown",
                )

    with tab_feedback:
        with st.container(border=True):
            st.markdown(feedback_text or "_No feedback generated._")

    with tab_search:
        with st.container(border=True):
            st.text_area(
                "Raw search results", state.get("search_results", ""), height=350,
                label_visibility="collapsed",
            )

    with tab_scraped:
        with st.container(border=True):
            st.text_area(
                "Scraped content", state.get("scraped_content", ""), height=350,
                label_visibility="collapsed",
            )