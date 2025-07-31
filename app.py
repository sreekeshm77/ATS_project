import streamlit as st
import requests
import json
import os
import fitz  # PyMuPDF for PDF
import docx2txt

# Load API key
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

SYSTEM_PROMPT_BASE = """
You are an AI-powered ATS Resume Evaluator.
Evaluate the candidate’s resume and (if available) compare it with a job description.

Return only in this JSON format:

{
  "ats_score": 0-100,
  "summary_feedback": "...",
  "skills_feedback": "...",
  "experience_feedback": "...",
  "education_feedback": "...",
  "pros": ["..."],
  "cons": ["..."],
  "recommendations": ["..."],
  "matched_keywords": ["..."],
  "missing_keywords": ["..."]
}
"""

def extract_text_from_pdf(uploaded_file):
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        return "\n".join([page.get_text() for page in doc])

def extract_text_from_docx(uploaded_file):
    return docx2txt.process(uploaded_file)

def extract_text_from_json(uploaded_file):
    try:
        raw = json.load(uploaded_file)
        return json.dumps(raw, indent=2)
    except Exception:
        return "Invalid JSON"

def call_groq_mistral(resume_text, job_description=""):
    user_prompt = f"""
Resume:
{resume_text}

Job Description:
{job_description if job_description else 'N/A'}
"""
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_BASE},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4
    }

    response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        try:
            return json.loads(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            st.error(f"Error parsing response: {e}")
    else:
        st.error(f"API error: {response.status_code} - {response.text}")
    return None

# Streamlit UI
st.set_page_config(page_title="AI ATS Resume Checker", layout="centered")
st.title("📄 AI-Powered ATS Resume Checker")
st.markdown("Upload your resume (PDF, DOCX, JSON). Job Description is optional for detailed feedback.")

resume_file = st.file_uploader("📁 Upload Resume", type=["pdf", "docx", "json"])
jd_input = st.text_area("💼 Paste Job Description (Optional)", height=200)

resume_text = ""

if resume_file:
    if resume_file.name.endswith(".pdf"):
        resume_text = extract_text_from_pdf(resume_file)
    elif resume_file.name.endswith(".docx"):
        resume_text = extract_text_from_docx(resume_file)
    elif resume_file.name.endswith(".json"):
        resume_text = extract_text_from_json(resume_file)
    else:
        st.warning("Unsupported file format.")

if st.button("🚀 Analyze Resume"):
    if resume_text.strip():
        with st.spinner("Analyzing resume with Mistral..."):
            result = call_groq_mistral(resume_text, jd_input)
        if result:
            st.success("✅ Analysis Complete")
            st.markdown(f"### 🎯 ATS Score: **{result['ats_score']} / 100**")
            st.subheader("🧩 Section Feedback")
            st.write("**Summary**:", result["summary_feedback"])
            st.write("**Skills**:", result["skills_feedback"])
            st.write("**Experience**:", result["experience_feedback"])
            st.write("**Education**:", result["education_feedback"])

            st.subheader("✅ Pros")
            st.markdown("\n".join([f"- {pro}" for pro in result["pros"]]))

            st.subheader("❌ Cons")
            st.markdown("\n".join([f"- {con}" for con in result["cons"]]))

            st.subheader("🛠️ Recommendations")
            st.markdown("\n".join([f"- {rec}" for rec in result["recommendations"]]))

            st.subheader("🔍 Keywords")
            st.write("**Matched:**", ", ".join(result["matched_keywords"]))
            st.write("**Missing:**", ", ".join(result["missing_keywords"]))
    else:
        st.warning("Please upload a resume to proceed.")
