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
        try:
            # --- ИЗМЕНЕНИЕ: Логотип шириной 75мм (было 15) ---
            self.image('logo.png', 10, 8, 75) 
        except:
            pass 
        # --- ИЗМЕНЕНИЕ: Отступ вниз 35мм, чтобы текст не наехал на большое лого ---
        self.ln(35) 

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 9) 
        self.cell(0, 10, 'Questions? Contact ahmlvs@aaadevs.com', 0, 0, 'C')

# Функция генерации контента (Ваш стабильный код)
def create_pdf(text_content):
    pdf = PDFReport()
    pdf.add_page()
    
    # --- НАСТРОЙКА ШРИФТОВ ---
    font_family = "Arial" 
    
    font_path = "DejaVuSans.ttf" 
    if os.path.exists(font_path):
        try:
            pdf.add_font('CustomFont', '', font_path, uni=True)
            pdf.add_font('CustomFont', 'B', font_path, uni=True)
            font_family = 'CustomFont'
        except:
            pass

    pdf.set_font(font_family, size=11)
    
    # --- УМНОЕ ФОРМАТИРОВАНИЕ ---
    lines = text_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(3) 
            continue
        
        # Безопасный блок: если строка ломает PDF, мы её пропускаем
        try:
            # 1. ЗАГОЛОВКИ (Header 1: #)
            if line.startswith('# '):
                clean_line = line.replace('# ', '').replace('**', '')
                pdf.ln(5)
                pdf.set_x(10)
                pdf.set_font(font_family, 'B', 16)
                pdf.multi_cell(0, 8, clean_line)
                pdf.set_font(font_family, '', 11) 
                
            # 2. ПОДЗАГОЛОВКИ (Header 2: ##)
            elif line.startswith('## '):
                clean_line = line.replace('## ', '').replace('**', '')
                pdf.ln(3)
                pdf.set_x(10)
                pdf.set_font(font_family, 'B', 13)
                pdf.multi_cell(0, 6, clean_line)
                pdf.set_font(font_family, '', 11)
                
            # 3. СПИСКИ (* или -)
            elif line.startswith('* ') or line.startswith('- '):
                clean_line = line[2:].replace('**', '') 
                pdf.set_x(15) 
                pdf.multi_cell(0, 5, '- ' + clean_line)
                
            # 4. ОБЫЧНЫЙ ТЕКСТ
            else:
                clean_line = line.replace('**', '').replace('__', '').replace('### ', '')
                pdf.set_x(10)
                pdf.multi_cell(0, 5, clean_line)
                
        except Exception as e:
            print(f"Error printing line: {e}")
            continue

    return bytes(pdf.output())

# --- EMAIL FUNCTION (MODIFIED) ---
def send_email(to_email, report_text, uploaded_file_obj, user_api_key, attach_source=True):
    if "EMAIL_USER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
        return 
    
    sender_email = st.secrets["EMAIL_USER"]
    sender_password = st.secrets["EMAIL_PASSWORD"]
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email # Динамический получатель
    msg['Subject'] = f"Your AI Readiness Report is Ready ({datetime.date.today()})"
    
    body = f"This marks the start of cutting costs and preparing your business for scaling.

Please note: As this is an automated report, it may contain minor discrepancies. 
If you need clarification or want to discuss "what's next", simply reply to this email. We are here to help!

Best regards,
AiAiAi Automation Team""
    msg.attach(MIMEText(body, 'plain'))
    
    # 1. Прикрепляем ГОТОВЫЙ ОТЧЕТ (PDF) - всегда
    try:
        pdf_bytes = create_pdf(report_text)
        part_pdf = MIMEBase('application', "pdf")
        part_pdf.set_payload(pdf_bytes)
        encoders.encode_base64(part_pdf)
        part_pdf.add_header('Content-Disposition', f'attachment; filename="Audit_Report_{datetime.date.today()}.pdf"')
        msg.attach(part_pdf)
    except Exception as e:
        print(f"Error attaching generated PDF: {e}")

    # 2. Прикрепляем ИСХОДНЫЙ ФАЙЛ - ТОЛЬКО ЕСЛИ НУЖНО
    if attach_source:
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

    # Отправка через ZOHO
    try:
        server = smtplib.SMTP('smtp.zoho.com', 587) # ZOHO SERVER
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
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
You must use English. 

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
Do NOT use a table.
You must GROUP and LIST the recommendations in the following strict order:

1. First, list all **Quick Wins** (High Impact / Low Effort).
2. Second, list all **Strategic Initiatives** (High Impact / High Effort).
3. Third, list all **Low Priority** items.

If a category has no items, omit it.

Format each entry strictly as follows:
* **[Priority Level] — [Process Name]**
    * **Solution Type:** [Optimization / RPA / AI]
    * **Rationale:** [Explanation based on volumes/time]

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

# Step 2 (MODIFIED: Added Email Input)
with col_step2:
    st.markdown('<div class="step-oval">Email & Agree</div>', unsafe_allow_html=True)
    
    # --- ИЗМЕНЕНИЕ: Обязательное поле для ввода Email ---
    user_email = st.text_input("Your Business Email", placeholder="name@company.com")
    
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
# Для центровки используем колонки 1-1-1
c1, c2, c3 = st.columns([1, 1, 1])

with c2:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key", type="password")

    if st.button("Get My AI-First Plan"):
        st.session_state.generated = True 
        
        # --- ВАЛИДАЦИЯ ---
        if not user_email:
             st.error("Please enter your email address.")
             st.session_state.generated = False
        elif "@" not in user_email: # Простая проверка
             st.error("Please enter a valid email address.")
             st.session_state.generated = False
        elif not agreement:
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
                        
                        # Модель
                        model = genai.GenerativeModel("gemini-flash-lite-latest", system_instruction=SYSTEM_PROMPT)
                        response = model.generate_content(f"Data:\n{raw_text}")
                        
                        st.session_state.report_text = response.text
                        
                        # --- ОТПРАВКА ПИСЕМ (ИЗМЕНЕНО) ---
                        
                        # 1. Отправка Админу (С исходником)
                        send_email("ahmlvs@aaadevs.com", response.text, uploaded_file, api_key, attach_source=True)
                        
                        # 2. Отправка Пользователю (Без исходника)
                        send_email(user_email, response.text, uploaded_file, api_key, attach_source=False)
                        
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

# --- Display Result (ИЗМЕНЕНО: Только сообщение об успехе) ---
if st.session_state.report_text:
    st.markdown("---")
    # Красивое сообщение об успехе по центру
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; color: #166534;">
        <h3 style="margin:0;">Success!</h3>
        <p style="font-size: 18px; margin-top: 10px;">
            Your AI readiness report has been generated and sent to <b>{user_email}</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Старый код отображения текста и кнопки удален для безопасности и UX

# Footer
st.markdown("""
<div class="whats-next">
    What's next? <br>
    <a href="mailto:ahmlvs@aaadevs.com?subject=Discussion%20about%20AI%20Audit">ahmlvs@aaadevs.com</a>
</div>
""", unsafe_allow_html=True)
