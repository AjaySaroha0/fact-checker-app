"""
app.py
Main Streamlit application for AI Fact Checker.
A modern, professional fact-checking platform.
"""

import os
import json
from datetime import datetime
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv

from search import SearchEngine, SearchError
from verifier import FactVerifier, VerificationError

# Load environment variables
load_dotenv()

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="AI Fact Checker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)


with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False


def get_verdict_class(verdict: str) -> str:
    """Get CSS class for verdict badge."""
    verdict_map = {
        "TRUE": "verdict-true",
        "FALSE": "verdict-false",
        "MISLEADING": "verdict-misleading",
        "PARTIALLY TRUE": "verdict-partially-true",
        "UNVERIFIED": "verdict-unverified",
        "SATIRE": "verdict-satire"
    }
    return verdict_map.get(verdict.upper(), "verdict-unverified")


def get_verdict_icon(verdict: str) -> str:
    """Get emoji icon for verdict."""
    icon_map = {
        "TRUE": "✅",
        "FALSE": "❌",
        "MISLEADING": "⚠️",
        "PARTIALLY TRUE": "🔄",
        "UNVERIFIED": "❓",
        "SATIRE": "😄"
    }
    return icon_map.get(verdict.upper(), "❓")


def add_to_history(result: Dict):
    """Add a result to search history."""
    history_item = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "claim": result.get("claim", "Unknown claim"),
        "verdict": result.get("verdict", "UNVERIFIED"),
        "confidence": result.get("confidence", 0)
    }

    # Add to beginning, keep max 20 items
    st.session_state.search_history.insert(0, history_item)
    if len(st.session_state.search_history) > 20:
        st.session_state.search_history = st.session_state.search_history[:20]


def download_result(result: Dict) -> str:
    """Format result for download."""
    download_text = f"""
AI FACT CHECK REPORT
{'=' * 50}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

CLAIM:
{result.get('claim', 'N/A')}

VERDICT: {result.get('verdict', 'N/A')}
CONFIDENCE: {result.get('confidence', 0)}%

SUMMARY:
{result.get('summary', 'N/A')}

DETAILED EXPLANATION:
{result.get('detailed_explanation', 'N/A')}

KEY EVIDENCE:
"""
    for evidence in result.get("key_evidence", []):
        download_text += f"- {evidence}\n"

    download_text += f"""
SOURCE RELIABILITY:
{result.get('source_reliability', 'N/A')}

FINAL CONCLUSION:
{result.get('final_conclusion', 'N/A')}

SOURCES:
"""
    for source in result.get("sources", []):
        download_text += f"- {source}\n"

    return download_text


# HEADER SECTION

st.markdown("""
<div class="title-container">
    <div class="main-title">🔍 AI Fact Checker</div>
    <div class="subtitle">Verify claims, detect misinformation, and analyze news with AI-powered fact-checking</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)


# SIDEBAR

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding-bottom: 1rem;">
        <h2 style="color: #00d4ff; font-size: 1.3rem;">📊 Search History</h2>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.search_history:
        for idx, item in enumerate(st.session_state.search_history):
            verdict_color = {
                "TRUE": "#00b894",
                "FALSE": "#e74c3c",
                "MISLEADING": "#e67e22",
                "PARTIALLY TRUE": "#f1c40f",
                "UNVERIFIED": "#95a5a6",
                "SATIRE": "#9b59b6"
            }.get(item["verdict"], "#95a5a6")

            st.markdown(f"""
            <div class="history-item">
                <div style="font-size: 0.75rem; color: #888; margin-bottom: 0.3rem;">{item['timestamp']}</div>
                <div style="font-weight: 500; color: #e0e0e0; margin-bottom: 0.3rem; font-size: 0.9rem;">{item['claim'][:60]}...</div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: {verdict_color}; font-weight: 600; font-size: 0.8rem;">{item['verdict']}</span>
                    <span style="color: #888; font-size: 0.8rem;">{item['confidence']}% confidence</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            No search history yet.<br>Start fact-checking to see results here!
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # About section
    with st.expander("ℹ️ About"):
        st.markdown("""
        **AI Fact Checker** uses advanced AI and real-time web search to verify claims and detect misinformation.

        **How it works:**
        1. Enter any claim, headline, or statement
        2. Our system searches the web for evidence
        3. AI analyzes the evidence and provides a verdict
        4. Get detailed reasoning with source links

        **Verdicts:**
        - ✅ **True** - Fully supported by evidence
        - ❌ **False** - Directly contradicted by evidence
        - ⚠️ **Misleading** - Distorted or out of context
        - 🔄 **Partially True** - Partially accurate
        - ❓ **Unverified** - Insufficient evidence
        - 😄 **Satire** - From satirical source
        """)

# =====================================================
# MAIN INPUT SECTION
# =====================================================
with st.container():
    st.markdown('<div class="input-section">', unsafe_allow_html=True)

    claim_input = st.text_area(
        "Enter a claim, news headline, or statement to verify:",
        placeholder="Example: NASA confirmed aliens landed in India",
        key="claim_input",
        help="Type or paste the claim you want to fact-check"
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        verify_button = st.button(
            "🔍 Verify Claim",
            key="verify_button",
            use_container_width=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# PROCESSING LOGIC
# =====================================================
if verify_button and claim_input.strip():
    # Validate input
    if len(claim_input.strip()) < 10:
        st.error("⚠️ Please enter a more detailed claim (at least 10 characters).")
        st.stop()

    st.session_state.is_processing = True

    # Show processing spinner
    with st.spinner("🔍 Searching the web and analyzing evidence... This may take a moment."):
        try:
            # Step 1: Search for evidence
            search_engine = SearchEngine()
            search_results = search_engine.search(claim_input.strip())

            if not search_results:
                st.warning("⚠️ No search results found. The claim may be too specific or there may be limited online sources.")
                st.stop()

            # Step 2: AI Analysis
            verifier = FactVerifier()
            result = verifier.verify(claim_input.strip(), search_results)

            # Store result
            st.session_state.current_result = result
            add_to_history(result)

        except SearchError as e:
            st.error(f"🔍 Search Error: {str(e)}")
            st.stop()
        except VerificationError as e:
            st.error(f"🤖 AI Analysis Error: {str(e)}")
            st.stop()
        except ValueError as e:
            st.error(f"⚙️ Configuration Error: {str(e)}")
            st.info("💡 Please make sure your API keys are set in the .env file.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Unexpected Error: {str(e)}")
            st.stop()
        finally:
            st.session_state.is_processing = False

elif verify_button and not claim_input.strip():
    st.warning("⚠️ Please enter a claim to verify.")

# =====================================================
# RESULTS DISPLAY
# =====================================================
if st.session_state.current_result:
    result = st.session_state.current_result

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Claim Display
    st.markdown(f"""
    <div class="claim-display">
        <strong>Claim:</strong> "{result.get('claim', '')}"
    </div>
    """, unsafe_allow_html=True)

    # Verdict and Confidence Row
    col1, col2 = st.columns([1, 1])

    with col1:
        verdict = result.get("verdict", "UNVERIFIED")
        verdict_class = get_verdict_class(verdict)
        verdict_icon = get_verdict_icon(verdict)

        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <div class="verdict-badge {verdict_class}">
                {verdict_icon} {verdict}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        confidence = result.get("confidence", 0)
        st.markdown(f"""
        <div class="confidence-container">
            <div class="confidence-label">Confidence Score</div>
            <div class="confidence-value">{confidence}%</div>
            <div style="margin-top: 0.5rem;">
                <div class="stProgress">
                    <div style="width: {confidence}%; height: 6px; background: linear-gradient(90deg, #00d4ff, #7b2cbf); border-radius: 3px;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Summary Card
    if result.get("summary"):
        st.markdown(f"""
        <div class="result-card">
            <div class="result-card-title">📋 Summary</div>
            <div class="result-card-content">{result['summary']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Detailed Explanation
    if result.get("detailed_explanation"):
        with st.expander("📖 Detailed Explanation", expanded=True):
            st.markdown(f"""
            <div class="result-card-content">
                {result['detailed_explanation']}
            </div>
            """, unsafe_allow_html=True)

    # Key Evidence
    if result.get("key_evidence"):
        with st.expander("🔑 Key Evidence", expanded=True):
            for evidence in result["key_evidence"]:
                st.markdown(f"""
                <div class="evidence-item">
                    {evidence}
                </div>
                """, unsafe_allow_html=True)

    # Source Reliability
    if result.get("source_reliability"):
        with st.expander("📊 Source Reliability Assessment"):
            st.markdown(f"""
            <div class="result-card-content">
                {result['source_reliability']}
            </div>
            """, unsafe_allow_html=True)

    # Final Conclusion
    if result.get("final_conclusion"):
        st.markdown(f"""
        <div class="result-card" style="border-color: rgba(0, 212, 255, 0.3);">
            <div class="result-card-title">🎯 Final Conclusion</div>
            <div class="result-card-content" style="font-weight: 500;">
                {result['final_conclusion']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Sources
    raw_sources = result.get("raw_sources", [])
    if raw_sources:
        with st.expander("🔗 Sources & References"):
            for source in raw_sources:
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                domain = source.get("source", "Unknown")
                snippet = source.get("snippet", "")[:150]

                st.markdown(f"""
                <div class="source-card">
                    <div class="source-title">{title}</div>
                    <div style="color: #aaa; font-size: 0.9rem; margin: 0.3rem 0;">{snippet}...</div>
                    <a href="{url}" target="_blank" class="source-url">{url}</a>
                    <div class="source-domain">📰 {domain}</div>
                </div>
                """, unsafe_allow_html=True)

    # Download Button
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        download_text = download_result(result)
        st.download_button(
            label="📥 Download Report",
            data=download_text,
            file_name=f"fact_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

# =====================================================
# FOOTER
# =====================================================
st.markdown("""
<div class="footer">
    <div class="custom-divider"></div>
    <p>🔍 AI Fact Checker | Powered by OpenAI & Tavily Search</p>
    <p style="font-size: 0.75rem; color: #555;">
        This tool provides analysis based on available web sources. Always verify critical information independently.
    </p>
</div>
""", unsafe_allow_html=True)