
import streamlit as st
import tempfile
import os
import httpx
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from PyPDF2 import PdfReader  # used for reading PDFs
from fpdf import FPDF
import pandas as pd

# ------------------- LLM Setup -------------------
client = httpx.Client(verify=False)
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-6xQ8EOKEoGZoa4snyZMaPw",
    http_client=client,
    streaming=True,
)

# ------------------- Streamlit Setup -------------------
st.set_page_config(
    page_title="BPR Suggestion Agent - Cognitive Innovators",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- Top Banner -------------------
BANNER_HTML = """
<div style="background: linear-gradient(90deg,#0f172a,#3b82f6); padding: 12px 20px; border-radius:8px; margin-bottom:10px;">
  <h2 style="color: white; margin:0; font-weight:600;">Gen Ai Friday Hackathon — Business Process Reengineering Suggestion Agent</h2>
</div>
"""
st.markdown(BANNER_HTML, unsafe_allow_html=True)

# ------------------- Sidebar / Navigation -------------------
st.sidebar.title("🧠 Cognitive Innovators")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "📊 Process Reengineering", "👥 About Team", "🔮 Upcoming Features"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 Cognitive Innovators")

# ------------------- HOME PAGE -------------------
if page == "🏠 Home":
    st.title("📊 Business Process Reengineering Suggestion Agent")
    st.markdown(
        """
        Welcome to **Business Process Reengineering Suggestion Agent** — built by **Cognitive Innovators**.

        Use the _Process Reengineering_ tab to upload documents (PDF/CSV/DOCX), provide brief descriptions,
        and generate AI-driven process improvement reports. You can download a personalized PDF report
        and ask follow-up questions.
        """
    )

# ------------------- MAIN ANALYSIS PAGE -------------------
elif page == "📊 Process Reengineering":
    st.title("📊 Process Reengineering Analysis")
    st.markdown("Upload your documents and receive a personalized AI-generated BPR report.")

    # User Details
    st.subheader("👤 User Details (used in report)")
    user_name = st.text_input("Your Name:", placeholder="e.g., A. Prasad")
    organization = st.text_input("Your Organization:", placeholder="e.g., ACME Manufacturing")

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload up to 5 documents (PDF, CSV, DOCX)",
        type=["pdf", "csv", "docx"],
        accept_multiple_files=True
    )

    # Optional file descriptions
    file_descriptions = {}
    if uploaded_files:
        st.subheader("📝 Describe Each File (Optional)")
        for f in uploaded_files:
            desc = st.text_area(f"Description for `{f.name}`", placeholder="(Optional) Explain what this document contains...")
            file_descriptions[f.name] = desc

    # Prompt Template (langchain_core)
    prompt_template = PromptTemplate(
        input_variables=["documents", "user", "org"],
        template="""
You are an AI Business Process Reengineering Expert for manufacturing. Do not hallucinate and give results within
the provided documents, refer only real fact data to generate result.

Generate a detailed report for:
- User: {user}
- Organization: {org}

Produce a structured improvement report including:
1) Overview of current process
2) Detected inefficiencies / bottlenecks
3) Proposed reengineering actions (detailed steps)
4) Expected business benefits (KPI impact estimates, timeline)
5) Benchmark comparisons if applicable
6) Automation & digitalization opportunities
7) Risks & mitigations

Use Lean, Six Sigma concepts where relevant and be concise and actionable.

Documents:
{documents}
"""
    )

    # Generate button
    if st.button("🔍 Generate Analysis Report"):
        if not user_name or not organization:
            st.warning("Please enter your name and organization before generating the report.")
        elif not uploaded_files:
            st.warning("Please upload at least one file.")
        else:
            with st.spinner("Analyzing documents..."):
                all_texts = []
                for uploaded_file in uploaded_files:
                    # write to temp file to read depending on type
                    temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.read())

                    ext = uploaded_file.name.split(".")[-1].lower()
                    text_content = ""
                    try:
                        if ext == "pdf":
                            reader = PdfReader(temp_path)
                            pages = []
                            for page in reader.pages:
                                # some pages may return None
                                txt = page.extract_text() or ""
                                pages.append(txt)
                            text_content = "\n".join(pages)
                        elif ext == "csv":
                            df = pd.read_csv(temp_path)
                            # convert to a compact string
                            text_content = df.to_string(max_rows=20, max_cols=8)
                        elif ext == "docx":
                            from docx import Document
                            doc = Document(temp_path)
                            paras = [p.text for p in doc.paragraphs]
                            text_content = "\n".join(paras)
                    except Exception as e:
                        text_content = f"[Error reading {uploaded_file.name}: {e}]"

                    desc = file_descriptions.get(uploaded_file.name, "")
                    snippet = text_content if len(text_content) < 5000 else text_content[:5000] + "\n[Truncated]"
                    all_texts.append(f"File: {uploaded_file.name}\nDescription: {desc}\nContent:\n{snippet}")

                combined_docs = "\n\n".join(all_texts)
                full_prompt = prompt_template.format(documents=combined_docs, user=user_name, org=organization)

                st.subheader("📈 Process Improvement Report")
                st.info("Generating report — streaming below (UI will show full text).")

                streamed_output = ""
                stream_container = st.empty()

                # llm.stream yields token-like chunks (implementation depends on your LangChain client)
                # We'll iterate and append content to the UI as it arrives.
                try:
                    for chunk in llm.stream(full_prompt):
                        # chunk may be a dict-like or object with .content depending on LangChain client
                        text_chunk = ""
                        if hasattr(chunk, "content"):
                            text_chunk = chunk.content or ""
                        elif isinstance(chunk, dict) and "content" in chunk:
                            text_chunk = chunk["content"] or ""
                        elif isinstance(chunk, str):
                            text_chunk = chunk
                        # append and render
                        if text_chunk:
                            streamed_output += text_chunk
                            stream_container.markdown(streamed_output)
                except Exception as err:
                    st.error(f"LLM streaming failed: {err}")
                    streamed_output = streamed_output or "[Partial output received]"

                st.success("✅ Analysis complete!")
                st.session_state["context"] = full_prompt + "\n\nLLM Response:\n" + streamed_output
                st.session_state["report"] = streamed_output

                # ---------------- Download PDF ----------------
                if streamed_output:
                    # FPDF sometimes fails on non-latin characters; sanitize for PDF
                    def sanitize_for_pdf(s: str) -> str:
                        # encode to latin-1 replacing unencodable chars, then decode back -> replaces with '?'
                        try:
                            return s.encode("latin-1", errors="replace").decode("latin-1")
                        except Exception:
                            # final fallback - strip non-ascii
                            return s.encode("ascii", errors="replace").decode("ascii")

                    safe_name = sanitize_for_pdf(user_name or "User")
                    safe_org = sanitize_for_pdf(organization or "Organization")
                    safe_report = sanitize_for_pdf(streamed_output)

                    pdf = FPDF()
                    pdf.set_auto_page_break(auto=True, margin=15)
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 14)
                    pdf.cell(0, 10, "Business Process Reengineering Report", ln=True, align="C")
                    pdf.ln(4)
                    pdf.set_font("Arial", size=11)
                    pdf.cell(0, 8, f"Name: {safe_name}", ln=True)
                    pdf.cell(0, 8, f"Organization: {safe_org}", ln=True)
                    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
                    pdf.ln(6)
                    pdf.set_font("Arial", size=10)
                    # break the report into lines for multi_cell safely
                    pdf.multi_cell(0, 6, safe_report)
                    pdf_path = os.path.join(tempfile.gettempdir(), f"BPR_Report_{safe_name}.pdf")
                    try:
                        pdf.output(pdf_path)
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="📥 Download Report as PDF",
                                data=pdf_file,
                                file_name=f"BPR_Report_{safe_name}.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Failed to generate PDF: {e}")
                        # As fallback, provide report as a text download
                        st.download_button(
                            label="📥 Download Report (TXT fallback)",
                            data=streamed_output,
                            file_name=f"BPR_Report_{safe_name}.txt",
                            mime="text/plain"
                        )

    # Follow-up Q&A
    if "context" in st.session_state:
        st.divider()
        st.subheader("💬 Ask Follow-Up Questions")
        user_query = st.text_input("Your question about the report:")
        if st.button("Ask"):
            if user_query.strip():
                followup_prompt = (
                    st.session_state["context"]
                    + f"\n\nUser follow-up question: {user_query}\nAnswer concisely based on the context."
                )
                st.info("Streaming follow-up answer...")
                followup_container = st.empty()
                response_text = ""
                try:
                    for chunk in llm.stream(followup_prompt):
                        text_chunk = ""
                        if hasattr(chunk, "content"):
                            text_chunk = chunk.content or ""
                        elif isinstance(chunk, dict) and "content" in chunk:
                            text_chunk = chunk["content"] or ""
                        elif isinstance(chunk, str):
                            text_chunk = chunk
                        if text_chunk:
                            response_text += text_chunk
                            followup_container.markdown(response_text)
                except Exception as err:
                    st.error(f"Follow-up streaming failed: {err}")
            else:
                st.warning("Please enter a question before clicking Ask.")

# ------------------- ABOUT TEAM PAGE -------------------
elif page == "👥 About Team":
    st.title("👥 Team: Cognitive Innovators")
    st.markdown("""
    **Cognitive Innovators** is a multidisciplinary AI research and development team focused on integrating
    Agentic AI with industrial process optimization and decision intelligence.

    **Vision:** Revolutionize process improvement and decision-making in enterprises through responsible, explainable, and scalable AI.

    **Core Competencies:**
    - AI-driven Business Process Reengineering
    - Manufacturing Intelligence and IoT integration
    - Predictive Process Optimization
    - Enterprise AI systems integration

    **Values:** Innovation | Integrity | Impact
    
    **Team Members** \n
        1. Aalekh Prasad (2797089) \n
        2. Nagendra Egyrapa (2445390) \n
        3. Ashwini kumar Singh (2844758) \n
        4. Tulsiram Pandipati (774827) \n
        5. Sajid shaik (1531648) \n
    """)

# ------------------- UPCOMING FEATURES PAGE -------------------
elif page == "🔮 Upcoming Features":
    st.title("🔮 Upcoming Features")
    st.markdown("""
    Planned enhancements:
    - Automated workflow simulation & visualization
    - KPI dashboard with before/after scenarios
    - Multi-agent optimization (cost/time/quality agents)
    - Voice-based interaction & mobile support
    - Persistent storage & enterprise connector (ERP/MES)
    """)
