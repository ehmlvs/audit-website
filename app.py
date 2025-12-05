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
You are a Senior Business Process Analyst and Intelligent Automation Expert. Your task is to analyze a completed questionnaire provided by a client and generate a formal Audit Report.

Strict Constraints:
1. Detect language of ANSWERS. Generate report in that language.
2. Fact-Based Analysis Only.
3. Date: {current_date}

Structure:
1. Executive Summary
2. Maturity Assessment (CMMI)
3. Process Deep Dive (Status, Pain Points, Recommendations: Optimization/RPA/AI)
4. Prioritization Matrix
5. Technology Landscape & Risks
6. Implementation Roadmap

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
