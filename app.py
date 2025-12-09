import streamlit as st
import google.generativeai as genai
import PyPDF2
import pandas as pd
import datetime
import io
import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF

# --- 1. Page Config ---
st.set_page_config(
    page_title="AiAiAi Automation",
    page_icon="△",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. Session State ---
if 'report_text' not in st.session_state:
    st.session_state.report_text = None
if 'generated' not in st.session_state:
    st.session_state.generated = False

# --- 3. Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,600;1,600&display=swap');

    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: 'Inter', sans-serif;
    }
    
    header, footer {visibility: hidden !important;}
    
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
    
    .step-arrow {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 50px;
        font-size: 24px;
        color: #000;
    }

    /* КНОПКА ПО ЦЕНТРУ */
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
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #f0f0f0 !important;
        border-color: #000 !important;
    }
    
    .whats-next {
        text-align: center;
        margin-top: 60px;
        font-family: 'Inter', sans-serif;
        color: #666;
        font-size: 16px;
    }
    .whats-next a {
        color: #000;
        text-decoration: none;
        font-weight: 600;
        border-bottom: 1px solid #000;
    }
</style>
""", unsafe_allow_html=True)


# --- 4. Logic Functions ---
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

# PDF Generation
class PDFReport(FPDF):
    def header(self):
        # Logo only
        try:
            self.image('logo.png', 10, 8, 15) 
        except:
            pass 
        self.ln(20)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 9) 
        self.cell(0, 10, 'Questions? Contact elena.hmelovs@gmail.com', 0, 0, 'C')

def create_pdf(text_content):
    pdf = PDFReport()
    pdf.add_page()
    
    # Имена твоих файловони лежат рядом с app.py
 
    font_reg = "DejaVuSans.ttf"
    font_bold = "DejaVuSans-Bold.ttf"
    font_italic = "DejaVuSans-Oblique.ttf"
    font_bold_italic = "DejaVuSans-BoldOblique.ttf"

    # Проверяем наличие основного шрифта
    if os.path.exists(font_reg):
        pdf.add_font('DejaVu', '', font_reg)           # Обычный
        
        # Подгружаем остальные стили, если файлы на месте
        if os.path.exists(font_bold):
            pdf.add_font('DejaVu', 'B', font_bold)     # Жирный
            
        if os.path.exists(font_italic):
            pdf.add_font('DejaVu', 'I', font_italic)   # Курсив
            
        if os.path.exists(font_bold_italic):
            pdf.add_font('DejaVu', 'BI', font_bold_italic) # Жирный курсив

        pdf.set_font('DejaVu', size=11)
    else:
        # Если шрифты не найдены, используем стандартный (но без кириллицы)
        pdf.set_font("Arial", size=11)
    
    # Включаем markdown=True для форматирования (**жирный**, *курсив*)
    pdf.multi_cell(0, 6, text_content, markdown=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- EMAIL FUNCTION ---
def send_email_to_admin(report_text, uploaded_file_obj, user_api_key):
    if "EMAIL_USER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
        return 
    
    sender_email = st.secrets["EMAIL_USER"]
    sender_password = st.secrets["EMAIL_PASSWORD"]
    receiver_email = "elena.hmelovs@gmail.com"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"New AI Audit Generated ({datetime.date.today()})"
    
    body = f"New lead generated an audit.\n\nAPI Key used: {user_api_key[:5]}..."
    msg.attach(MIMEText(body, 'plain'))
    
    # 1. Прикрепляем ГОТОВЫЙ ОТЧЕТ (PDF)
    try:
        pdf_bytes = create_pdf(report_text)
        part_pdf = MIMEBase('application', "pdf")
        part_pdf.set_payload(pdf_bytes)
        encoders.encode_base64(part_pdf)
        part_pdf.add_header('Content-Disposition', f'attachment; filename="Audit_Report_{datetime.date.today()}.pdf"')
        msg.attach(part_pdf)
    except Exception as e:
        print(f"Error attaching generated PDF: {e}")

    # 2. Прикрепляем ИСХОДНЫЙ ФАЙЛ (Анкету)
    try:
        uploaded_file_obj.seek(0)
        file_data = uploaded_file_obj.read()
        filename = uploaded_file_obj.name
        
        # Определяем MIME-тип
        if filename.endswith('.xlsx'):
            maintype, subtype = 'application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.pdf'):
            maintype, subtype = 'application', 'pdf'
        else:
            maintype, subtype = 'application', 'octet-stream'

        part_orig = MIMEBase(maintype, subtype)
        part_orig.set_payload(file_data)
        encoders.encode_base64(part_orig)
        part_orig.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part_orig)
    except Exception as e:
        print(f"Error attaching source file: {e}")

    # Отправка
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
    except Exception as e:
        print(f"Email error: {e}")

current_date = datetime.date.today().strftime("%B %d, %Y")

# --- 5. FULL SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
You are a Senior Business Process Analyst and Intelligent Automation Expert. Your task is to analyze a completed questionnaire provided by a client and generate a formal Report focused on automation potential.

Input Data Context:
The input will be a dataset (CSV or list) containing questions and answers for a single company.
If the company name is not explicitly stated in the data, refer to it simply as "The Company".

Strict Constraints & Guardrails:
Fact-Based Analysis Only: Base your analysis STRICTLY on the provided answers. Do not invent, assume, or hallucinate details.
Example: If the input mentions "Trello is used for tasks," do NOT assume "passwords are stored insecurely in Trello" unless the text explicitly says so.
If data is missing for a specific section, state: "Insufficient data provided."
Formal Tone: Use professional Business language.
Avoid informal language, slang, idioms (e.g., "heroism", "mess", "on the fly"), or emotive punctuation (!).
Use professional terms: instead of "chaos," use "lack of standardization"; instead of "heroism," use "high dependency on key personnel."
No tables allowed. You are strictly forbidden from using Markdown tables (do not use pipes | or rows). Whenever you would normally use a table you must use a structured bulleted list or nested list with bold headers instead.

TERMINOLOGY RULE: 
Use professional, native terminology. Never use direct translations like 'Аудитный'. Use 'Аудиторский отчет' or 'Отчет по аудиту' instead.

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
Model Overview: Provide a brief description of the CMMI (Capability Maturity Model Integration) framework and a short summary of its five levels (Initial, Managed, Defined, Quantitatively Managed, Optimizing) to establish context for the reader
.
Company Assessment: Assign a specific level (1-5) to The Company.
Justification: Justify the assigned level using specific evidence from the answers (e.g., "Level 2 because processes are repeatable but rely on specific individuals...").
Data Readiness Index: Assess the quality and structure of data (e.g., structured databases vs. unstructured PDFs/Excel).

3. Process Deep Dive 
Analyze the specific domains mentioned in the questionnaire (e.g., Procurement, Sales, HR, Finance). For each domain present:
Current Status: Facts from the input (volumes, formats, systems used).
Pain Points / Bottlenecks: Identified inefficiencies (manual entry, delays, errors).
Recommendation: Propose a specific solution classified as Process Optimization, RPA, or AI.

4. Prioritization Matrix 
Do NOT use a table. Instead, provide a structured list sorted by priority.
Format each entry strictly as follows:
[Priority Level: Quick Win / Strategic / Low Priority] — [Process Name]
Solution Type: [Optimization / RPA / AI]
Rationale: [Explanation based on volumes/time]

5. Technology Landscape & Risks
Current Stack: List systems mentioned in the input.
Risks: Identify risks (e.g., security, bus factor, data integrity) based only on the provided answers.

6. Implementation Roadmap
Propose a 3-phase plan (e.g., Phase 1: Foundation, Phase 2: Pilot, Phase 3: Scaling).
Constraint: Ensure every step in the roadmap corresponds to a finding in Section 3.

Use Markdown formatting (Headers, Bold, Lists), but strictly NO TABLES.
"""

# --- 6. Layout ---

# Logo
st.markdown("""
<div class="logo-container">
    <div class="logo-icon">△</div>
    <div>AiAiAi Automation</div>
</div>
""", unsafe_allow_html=True)

# Hero
st.markdown("""
<div class="hero-title">
    One minute to <br>
    check <span class="hero-italic">AI readiness</span>
</div>
""", unsafe_allow_html=True)

# Steps Grid
col_step1, col_arr1, col_step2, col_arr2, col_step3 = st.columns([3, 0.5, 3, 0.5, 3])

# Step 1
with col_step1:
    st.markdown('<div class="step-oval">Fill the form</div>', unsafe_allow_html=True)
    try:
        with open("Template.xlsx", "rb") as file:
            st.download_button("▼ Download Template", file, "Template.xlsx", key="dl_tmpl")
    except:
        st.error("Template missing")

# Arrow 1
with col_arr1:
    st.markdown('<div class="step-arrow">→</div>', unsafe_allow_html=True)

# Step 2
with col_step2:
    st.markdown('<div class="step-oval">Agree to rules</div>', unsafe_allow_html=True)
    
    agreement = st.checkbox("I agree to Terms & Conditions")
    
    # Кнопка скачивания Terms
    try:
        with open("terms.pdf", "rb") as f:
            st.download_button("📄 Download Terms", f, "terms.pdf", key="dl_terms")
    except:
        pass

# Arrow 2
with col_arr2:
    st.markdown('<div class="step-arrow">→</div>', unsafe_allow_html=True)

# Step 3
with col_step3:
    st.markdown('<div class="step-oval">Upload answers</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["xlsx", "xls", "pdf"], label_visibility="collapsed")


st.markdown("<br><br>", unsafe_allow_html=True)

# --- Main Button (Centered) ---
c1, c2, c3 = st.columns([1, 1, 1])

with c2:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key", type="password")

    if st.button("Get My AI-First Plan"):
        st.session_state.generated = True 
        
        if not agreement:
            st.error("Please agree to the Terms and Conditions.")
            st.session_state.generated = False
        elif not uploaded_file:
            st.error("Please upload your filled questionnaire.")
            st.session_state.generated = False
        elif not api_key:
            st.error("API Key missing.")
            st.session_state.generated = False
        else:
            with st.spinner("Analyzing your business DNA..."):
                # --- RETRY LOGIC (Защита от ошибки 429) ---
                max_retries = 3
                success = False
                
                for attempt in range(max_retries):
                    try:
                        genai.configure(api_key=api_key)
                        
                        file_ext = uploaded_file.name.split(".")[-1].lower()
                        if file_ext in ["xlsx", "xls"]:
                            raw_text = extract_text_from_excel(uploaded_file)
                        else:
                            raw_text = extract_text_from_pdf(uploaded_file)
                        
                        if not raw_text or len(raw_text) < 10:
                            st.error("File seems empty.")
                            break
                        
                        # --- ВАЖНО: Модель gemini-flash-latest для стабильности ---
                        model = genai.GenerativeModel("gemini-flash-latest", system_instruction=SYSTEM_PROMPT)
                        response = model.generate_content(f"Data:\n{raw_text}")
                        
                        st.session_state.report_text = response.text
                        
                        # Отправка почты
                        send_email_to_admin(response.text, uploaded_file, api_key)
                        success = True
                        break # Выходим из цикла
                        
                    except Exception as e:
                        # Если ошибка 429
                        if "429" in str(e) or "resource" in str(e).lower():
                            if attempt < max_retries - 1:
                                st.toast(f"AI is busy, retrying in 10 seconds... (Attempt {attempt+1}/{max_retries})")
                                time.sleep(10)
                                continue
                        
                        # Другие ошибки
                        st.error(f"Error: {e}")
                        st.session_state.generated = False
                        break


# --- Display Result ---
if st.session_state.report_text:
    st.success("Plan Generated Successfully!")
    st.markdown("---")
    st.markdown(st.session_state.report_text)
    
    # Кнопка скачивания PDF (по центру)
    try:
        pdf_bytes = create_pdf(st.session_state.report_text)
        
        d1, d2, d3 = st.columns([1, 1, 1])
        with d2:
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"AI_First_Plan_{datetime.date.today()}.pdf",
                mime="application/pdf"
            )
    except Exception as pdf_err:
        st.error(f"PDF Error: {pdf_err}")


# Footer
st.markdown("""
<div class="whats-next">
    What's next? <br>
    <a href="mailto:elena.hmelovs@gmail.com?subject=Discussion%20about%20AI%20Audit">elena.hmelovs@gmail.com</a>
</div>
""", unsafe_allow_html=True)
