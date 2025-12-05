import streamlit as st
import google.generativeai as genai
import PyPDF2
import pandas as pd
import datetime
import io

# --- 1. Page Config (Must be first) ---
st.set_page_config(
    page_title="AiAiAi Automation",
    page_icon="△",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. Custom CSS (The Design Magic) ---
st.markdown("""
<style>
    /* Подключаем шрифты: Playfair Display для заголовков, Inter для текста */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,600;1,600&display=swap');

    /* Глобальный сброс цветов Streamlit */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: 'Inter', sans-serif;
    }
    
    /* Скрываем стандартный хедер и футер */
    header, footer {visibility: hidden !important;}
    
    /* Стили для Логотипа */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'Playfair Display', serif;
        font-size: 24px;
        color: #000;
        margin-bottom: 60px;
    }
    .logo-icon {
        border: 1px solid black;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }

    /* Главный заголовок (Hero) */
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 80px;
        line-height: 1.1;
        text-align: center;
        font-weight: 400;
        margin-bottom: 80px;
        color: #1a1a1a;
    }
    .hero-italic {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-weight: 600;
    }

    /* Овальные рамки шагов */
    .step-oval {
        border: 1px solid #000000;
        border-radius: 50px;
        padding: 12px 20px;
        text-align: center;
        font-size: 18px;
        font-weight: 400;
        margin-bottom: 20px;
        background: white;
        white-space: nowrap;
    }
    
    /* Стрелка между шагами */
    .step-arrow {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 50px; /* Высота овала */
        font-size: 24px;
        color: #000;
    }

    /* Кастомная кнопка (Главная) */
    div.stButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid black !important;
        border-radius: 50px !important;
        padding: 15px 40px !important;
        font-size: 22px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        display: block;
        margin: 0 auto;
        box-shadow: none !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #f0f0f0 !important;
        border-color: #000 !important;
        transform: scale(1.02);
    }
    
    /* Стилизация File Uploader (насколько возможно) */
    .stFileUploader {
        padding-top: 0px;
    }
    
    /* Убираем лишние отступы */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 5rem;
    }
</style>
""", unsafe_allow_html=True)


# --- 3. Helper Functions (Logic) ---
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

# --- 4. System Prompt ---
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
Model Overview: Provide a brief description of the CMMI (Capability Maturity Model Integration) framework and a short summary of its five levels (Initial, Managed, Defined, Quantitatively Managed, Optimizing) to establish context for the reader.
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

Use Markdown.
"""

# --- 5. UI Layout Implementation ---

# -- A. Logo Section --
st.markdown("""
<div class="logo-container">
    <div class="logo-icon">△</div>
    <div>AiAiAi Automation</div>
</div>
""", unsafe_allow_html=True)

# -- B. Hero Section --
st.markdown("""
<div class="hero-title">
    One minute to <br>
    go <span class="hero-italic">AI first</span>
</div>
""", unsafe_allow_html=True)

# -- C. The "3 Steps" Flow --
# Создаем сложную сетку колонок: [Шаг 1] [Стрелка] [Шаг 2] [Стрелка] [Шаг 3]
# Используем соотношение ширины, чтобы это выглядело красиво
col_step1, col_arr1, col_step2, col_arr2, col_step3 = st.columns([3, 0.5, 3, 0.5, 3])

# --- STEP 1: Fill the form ---
with col_step1:
    st.markdown('<div class="step-oval">Fill the form</div>', unsafe_allow_html=True)
    
    # Кнопка скачивания, стилизованная под ссылку с треугольником
    try:
        with open("Template.xlsx", "rb") as file:
            st.download_button(
                label="▼ Download the Template",
                data=file,
                file_name="Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_btn"
            )
    except FileNotFoundError:
        st.error("Template.xlsx missing")

# --- ARROW 1 ---
with col_arr1:
    st.markdown('<div class="step-arrow">→</div>', unsafe_allow_html=True)

# --- STEP 2: Agree to rules ---
with col_step2:
    st.markdown('<div class="step-oval">Agree to rules</div>', unsafe_allow_html=True)
    
    # Чекбокс
    st.markdown("<br>", unsafe_allow_html=True) # Небольшой отступ
    agreement = st.checkbox("I agree to Terms and Conditions")

# --- ARROW 2 ---
with col_arr2:
    st.markdown('<div class="step-arrow">→</div>', unsafe_allow_html=True)

# --- STEP 3: Upload answers ---
with col_step3:
    st.markdown('<div class="step-oval">Upload answers</div>', unsafe_allow_html=True)
    
    # Загрузчик файлов
    uploaded_file = st.file_uploader("", type=["xlsx", "xls", "pdf"], label_visibility="collapsed")


# -- D. Spacer --
st.markdown("<br><br>", unsafe_allow_html=True)

# -- E. Main CTA Button & Logic --
# Чтобы центрировать кнопку, используем колонки
_, col_btn, _ = st.columns([1, 2, 1])

with col_btn:
    # API Key Logic (Hidden)
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        # Fallback for local testing
        api_key = st.text_input("API Key", type="password")

    # THE BUTTON
    start_audit = st.button("Get My AI-First Plan")


# --- 6. Execution ---
if start_audit:
    if not agreement:
        st.error("Please agree to the Terms and Conditions in Step 2.")
    elif not uploaded_file:
        st.error("Please upload your filled questionnaire in Step 3.")
    elif not api_key:
        st.error("System Error: API Key missing.")
    else:
        # Show spinner while working
        with st.spinner("Analyzing your business DNA..."):
            try:
                genai.configure(api_key=api_key)
                
                # 1. Extract
                file_ext = uploaded_file.name.split(".")[-1].lower()
                if file_ext in ["xlsx", "xls"]:
                    raw_text = extract_text_from_excel(uploaded_file)
                else:
                    raw_text = extract_text_from_pdf(uploaded_file)
                
                if not raw_text or len(raw_text) < 10:
                    st.error("File seems empty.")
                else:
                    # 2. Analyze (Using 2.0 Flash as preferred)
                    model = genai.GenerativeModel(
                        model_name="gemini-2.0-flash", 
                        system_instruction=SYSTEM_PROMPT
                    )
                    
                    response = model.generate_content(f"Data:\n{raw_text}")
                    
                    # 3. Success UI
                    st.success("Plan Generated Successfully!")
                    st.markdown("---")
                    st.markdown(response.text)
                    
                    st.download_button(
                        label="📥 Download Full Report",
                        data=response.text,
                        file_name=f"AI_First_Plan_{datetime.date.today()}.md",
                        mime="text/markdown"
                    )
                    
            except Exception as e:
                st.error(f"Error: {e}")
