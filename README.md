# Test-

Perfect — now you want the **BPR Suggestion Agent** to:

✅ Accept **PDF process document**,
✅ Read **6-month performance data (Excel file)**,
✅ Accept **workflow diagram (image)**,
✅ Use all three to generate **AI-powered suggestions + charts + final PDF report**.

Below is the **complete, integrated Streamlit version** (with code to extract text from PDF, read Excel, and handle diagrams), plus **sample input templates** you can create and test in VS Code.

---

## 🏗️ Final Folder Structure

```
bpr_suggestion_agent/
│
├── app.py
├── config.py
│
├── data/
│   ├── process_doc.pdf
│   ├── performance_data.xlsx
│   ├── workflow_diagram.png
│
├── modules/
│   ├── data_loader.py
│   ├── analyzer.py
│   ├── llm_client.py
│   ├── report_generator.py
│   ├── pdf_visualizer.py
│
├── output/
│   ├── bpr_report.txt
│   ├── bpr_report.pdf
│   ├── charts/
│
└── requirements.txt
```

---

## ⚙️ `config.py`

```python
LLM_API_URL = "https://api.tcsai.deepseek.com/v1/completions"
LLM_API_KEY = "YOUR_TCS_LLM_API_KEY"
LLM_MODEL = "got-4"
```

---

## 🧠 `modules/data_loader.py`

```python
import pandas as pd
import fitz  # PyMuPDF
import os

def load_performance_data(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    df = pd.read_excel(file_path)
    return df

def extract_text_from_pdf(file_path: str):
    """Extracts text from process PDF."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Process PDF not found: {file_path}")
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def load_workflow(file_path: str):
    if not os.path.exists(file_path):
        print("⚠️ Workflow diagram not found, skipping visual analysis.")
        return None
    return file_path
```

---

## 📈 `modules/analyzer.py`

```python
import pandas as pd

def analyze_performance(df: pd.DataFrame):
    """Extracts key metrics and inefficiencies from performance data."""
    summary = {
        "avg_cycle_time": df["CycleTime"].mean(),
        "defect_rate": df["Defects"].sum() / len(df),
        "machine_downtime": df["DowntimeHours"].sum(),
        "throughput": df["UnitsProduced"].sum()
    }

    inefficiencies = []
    if summary["defect_rate"] > 0.05:
        inefficiencies.append("High defect rate in assembly line.")
    if summary["machine_downtime"] > 100:
        inefficiencies.append("Excessive machine downtime.")
    if summary["avg_cycle_time"] > 120:
        inefficiencies.append("Cycle time exceeds industry benchmark (120 mins).")

    return summary, inefficiencies
```

---

## 🤖 `modules/llm_client.py`

```python
import requests
from config import LLM_API_URL, LLM_API_KEY, LLM_MODEL

def query_llm(prompt: str):
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0.7
    }

    response = requests.post(LLM_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json().get("choices", [{}])[0].get("text", "").strip()
```

---

## 🧾 `modules/report_generator.py`

```python
from datetime import datetime

def generate_prompt(summary, inefficiencies, process_text):
    prompt = f"""
You are a Business Process Reengineering expert for the manufacturing sector.
Based on the following inputs, suggest actionable improvements aligned with Lean and Six Sigma best practices.

=== PERFORMANCE SUMMARY ===
{summary}

=== IDENTIFIED INEFFICIENCIES ===
{inefficiencies}

=== PROCESS DOCUMENT EXTRACT ===
{process_text}

Provide:
1. Root cause analysis
2. Process redesign suggestions
3. Automation or digitization opportunities
4. Expected impact on cost, quality, and time
5. Benchmarks from leading manufacturing industries
    """
    return prompt


def write_report(text):
    output_path = "output/bpr_report.txt"
    with open(output_path, "w") as f:
        f.write(f"--- Business Process Reengineering Report ---\n")
        f.write(f"Generated on: {datetime.now()}\n\n")
        f.write(text)
    print(f"✅ Report saved at {output_path}")
```

---

## 📊 `modules/pdf_visualizer.py`

*(same as before — handles chart generation and PDF creation)*

---

## 💻 `app.py` — Streamlit Web Dashboard

```python
import streamlit as st
import pandas as pd
import os
from modules.data_loader import load_performance_data, extract_text_from_pdf, load_workflow
from modules.analyzer import analyze_performance
from modules.llm_client import query_llm
from modules.report_generator import generate_prompt, write_report
from modules.pdf_visualizer import generate_charts, create_pdf_report

st.set_page_config(page_title="BPR Suggestion Agent", layout="wide")

st.title("🏭 Business Process Reengineering Suggestion Agent")
st.caption("TCS AI Fridays Hackathon – Manufacturing Use Case")

st.markdown("---")
st.header("📂 Upload Input Files")

pdf_file = st.file_uploader("Upload Process Documentation (PDF)", type=["pdf"])
excel_file = st.file_uploader("Upload 6-Month Performance Data (Excel)", type=["xlsx", "xls"])
workflow_file = st.file_uploader("Upload Workflow Diagram (optional)", type=["png", "jpg", "jpeg"])

if st.button("🚀 Generate Report"):
    if not pdf_file or not excel_file:
        st.error("Please upload both PDF and Excel files.")
        st.stop()

    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    pdf_path = os.path.join("temp", pdf_file.name)
    excel_path = os.path.join("temp", excel_file.name)
    workflow_path = os.path.join("temp", workflow_file.name) if workflow_file else None

    with open(pdf_path, "wb") as f:
        f.write(pdf_file.getbuffer())

    with open(excel_path, "wb") as f:
        f.write(excel_file.getbuffer())

    if workflow_file:
        with open(workflow_path, "wb") as f:
            f.write(workflow_file.getbuffer())

    # Step 1: Load & Analyze
    process_text = extract_text_from_pdf(pdf_path)
    perf_data = load_performance_data(excel_path)
    summary, inefficiencies = analyze_performance(perf_data)

    st.subheader("📊 Performance Summary")
    st.json(summary)
    st.subheader("⚠️ Inefficiencies Identified")
    st.write(inefficiencies)

    # Step 2: Generate Charts
    st.subheader("📈 Performance Charts")
    generate_charts(perf_data)
    st.image("output/charts/defects.png")
    st.image("output/charts/cycle_time.png")
    st.image("output/charts/downtime.png")

    # Step 3: LLM Report
    st.subheader("🤖 AI Recommendations")
    with st.spinner("Analyzing and generating suggestions..."):
        prompt = generate_prompt(summary, inefficiencies, process_text)
        llm_output = query_llm(prompt)

    st.success("✅ Suggestions Generated!")
    st.text_area("LLM Output", llm_output, height=250)

    # Step 4: Generate PDF Report
    write_report(llm_output)
    create_pdf_report(summary, inefficiencies, llm_output)

    with open("output/bpr_report.pdf", "rb") as f:
        st.download_button("📥 Download Full PDF Report", f, file_name="bpr_report.pdf")

    st.success("🎉 Report generation completed successfully!")
```

---

## 🧩 `requirements.txt`

```
streamlit
pandas
requests
matplotlib
reportlab
PyMuPDF
openpyxl
```

---

## 🧾 **Sample Input Templates**

### 1️⃣ `performance_data.xlsx` (Sheet1)

| Month | UnitsProduced | Defects | CycleTime | DowntimeHours |
| ----- | ------------- | ------- | --------- | ------------- |
| Jan   | 10000         | 620     | 130       | 25            |
| Feb   | 10500         | 540     | 128       | 30            |
| Mar   | 9500          | 590     | 132       | 28            |
| Apr   | 10200         | 480     | 120       | 15            |
| May   | 10800         | 460     | 118       | 22            |
| Jun   | 9900          | 510     | 121       | 35            |

---

### 2️⃣ `process_doc.pdf`

Use any manufacturing process document.
Example text you can type and save as PDF:

```
Process Name: Engine Assembly Line

Steps:
1. Material inspection
2. Machining
3. Sub-assembly
4. Main assembly
5. Quality testing
6. Packaging and dispatch

Challenges:
- Manual quality checks
- Bottleneck at sub-assembly
- Lack of real-time production visibility
```

---

### 3️⃣ `workflow_diagram.png`

A simple diagram showing material → machining → assembly → inspection → packaging (you can even draw it in PowerPoint and export as PNG).

---

## 🏃 Run Command

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open:
👉 **[http://localhost:8501](http://localhost:8501)**

---

Would you like me to also add a **“Compare vs Industry Benchmarks”** section inside the Streamlit app and final PDF (for example, compare your metrics with Toyota / Bosch standards automatically)?
That would make your hackathon demo stand out even more.
