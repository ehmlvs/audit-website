import streamlit as st
import google.generativeai as genai
import PyPDF2
import pandas as pd
import datetime
import io

# --- 1. Page Config ---
st.set_page_config(page_title="AI Business Process Audit", page_icon="📊", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. Helper Functions ---
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_excel(file):
    try:
        df_dict = pd.read_excel(file, sheet_name=None)
        text = ""
        for sheet_name, df in df_dict.items():
            text += f"\n--- SHEET: {sheet_name} ---\n"
            text += df.to_string()
        return text
    except Exception as e:
        return f"Error reading Excel: {e}"

current_date = datetime.date.today().strftime("%B %d, %Y")

# --- 3. System Prompt ---
SYSTEM_PROMPT = f"""
You are a Senior Business Process Analyst and Intelligent Automation Expert. Your task is to analyze a completed questionnaire provided by a client and generate a formal Audit Report focused on automation potential.

Input Data Context:
The input will be a dataset (CSV or list) containing questions and answers for a single company.
If the company name is not explicitly stated in the data, refer to it simply as "The Company".

Strict Constraints & Guardrails:
Fact-Based Analysis Only: Base your analysis STRICTLY on the provided answers. Do not invent, assume, or hallucinate details.
Example: If the input mentions "Trello is used for tasks," do NOT assume "passwords are stored insecurely in Trello" unless the text explicitly says so.
If data is missing for a specific section, state: "Insufficient data provided."

Formal Tone: Use professional Business Language.
Avoid informal language, slang, idioms (e.g., "heroism", "mess", "on the fly"), or emotive punctuation (!).
Use professional terms: instead of "chaos," use "lack of standardization"; instead of "heroism," use "high dependency on key personnel."

Language:
You must detect the language used in the ANSWERS.
Example: If questions are in English but answers are in Hindi, the target language is Hindi.
The ENTIRE REPORT must be written in the detected language of the answers. Translate all headers, titles, bullet points, and analysis into that language. Do NOT mix languages.

The date of the report is {current_date}

Logical Consistency: The "Roadmap" section must directly address the findings in the "Process Analysis." Do not suggest a solution (e.g., "Create contract templates") in the Roadmap if the Analysis did not identify a lack of templates as a problem.

Classification of Recommendations: You must categorize every recommendation into exactly one of these three types:
Process Optimization / Standardization: (e.g., creating regulations, moving from Excel to SaaS, organizing file structures, eliminating duplicates).
RPA (Robotic Process Automation): (e.g., rule-based data transfer between systems, automatic notifications, simple if-then logic).
AI (Artificial Intelligence): (e.g., OCR, NLP, Generative AI, predictive analytics).

Report Structure:
1. Executive Summary
Company Overview: Brief description of the industry, scale, and size based only on the input data.
Current State Assessment: High-level summary of the process maturity.
Key Conclusion: The primary opportunity for improvement.

2. Maturity Assessment
Model Overview: Provide a brief description of the CMMI (Capability Maturity Model Integration) framework and a short summary of its five levels (Initial, Managed, Defined, Quantitatively Managed, Optimizing) to establish context for the reader [Image of CMMI Maturity Levels].
Company Assessment: Assign a specific level (1-5) to The Company.
Justification: Justify the assigned level using specific evidence from the answers (e.g., "Level 2 because processes are repeatable but rely on specific individuals...").
Data Readiness Index: Assess the quality and structure of data (e.g., structured databases vs. unstructured PDFs/Excel).

3. Process Deep Dive 
Analyze the specific domains mentioned in the questionnaire (e.g., Procurement, Sales, HR, Finance). For each domain present:
Current Status: Facts from the input (volumes, formats, systems used).
Pain Points / Bottlenecks: Identified inefficiencies (manual entry, delays, errors).
Recommendation: Propose a specific solution classified as Process Optimization, RPA, or AI.

4. Prioritization Matrix 
Create a table with the following columns:
Priority: (Quick Win, Strategic, or Low Priority).
Process: (Name of the process).
Solution Type: (Optimization / RPA / AI).
Rationale: Based on the volumes (time/quantity) provided in the input.

5. Technology Landscape & Risks
Current Stack: List systems mentioned in the input.
Risks: Identify risks (e.g., security, bus factor, data integrity) based only on the provided answers.

6. Implementation Roadmap
Propose a 3-phase plan (e.g., Phase 1: Foundation, Phase 2: Pilot, Phase 3: Scaling).
Constraint: Ensure every step in the roadmap corresponds to a finding in Section 3.

Use Markdown formatting.
"""

# --- 4. Sidebar ---
with st.sidebar:
    st.header("📂 Step 1: Get the Template")
    st.write("Please download and fill out the questionnaire.")
    try:
        with open("Template.xlsx", "rb") as file:
            st.download_button(
                label="📥 Download Excel Template",
                data=file,
                file_name="Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except FileNotFoundError:
        st.error("⚠️ 'Template.xlsx' not found. Please upload it to GitHub.")

    st.divider()
    
    # --- MODEL SELECTOR ---
    model_options = [
        "gemini-2.0-flash", 
        "gemini-2.0-pro-exp-02-05", 
        "gemini-2.0-flash-exp",
        "gemini-2.5-flash"
    ]
    selected_model_name = st.selectbox("AI Model Version", model_options, index=0)
    
    st.write("**Support:** support@aiaiaiautomation.com")

# --- 5. Main Content ---
st.title("📊 AI Business Process Audit")
st.markdown("**Get a professional audit of your business processes in 60 seconds.**")
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("User Details")
    user_email = st.text_input("Your Email", placeholder="name@company.com")
with col2:
    st.subheader("Step 2: Upload Data")
    uploaded_file = st.file_uploader("Upload filled questionnaire", type=["xlsx", "xls", "pdf"])

st.markdown("### 🔒 Terms & Conditions")
agreement = st.checkbox("I agree to the processing of personal data.")

# API Key Handling
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.text_input("Enter Google Gemini API Key", type="password")

# --- 6. Execution Logic ---
if st.button("🚀 Generate Audit Report"):
    if not agreement or not uploaded_file or not api_key:
        st.error("Please ensure you accepted terms, uploaded a file, and have an API key.")
    else:
        genai.configure(api_key=api_key)
        
        with st.spinner("🤖 AI is analyzing..."):
            try:
                # 1. Read File
                file_ext = uploaded_file.name.split(".")[-1].lower()
                if file_ext in ["xlsx", "xls"]:
