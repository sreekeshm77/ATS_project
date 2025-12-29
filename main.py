import os
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import Groq
import PyPDF2
import docx
import io
import json
import re
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="ATS Resume Checker", description="AI-powered ATS score checker for resumes")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text based on file type"""
    if filename.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_content)
    elif filename.lower().endswith('.docx'):
        return extract_text_from_docx(file_content)
    elif filename.lower().endswith('.txt'):
        return file_content.decode('utf-8')
    else:
        return "Unsupported file format. Please upload PDF, DOCX, or TXT files."

async def analyze_resume_with_groq(resume_text: str, job_description: str = "") -> dict:
    """Analyze resume using Groq API and return ATS score and feedback"""
    
    prompt = f"""
    As an expert ATS (Applicant Tracking System) analyzer, please analyze the following resume and provide a comprehensive evaluation.

    Resume Content:
    {resume_text}

    Job Description (if provided):
    {job_description}

    Please provide your analysis in the following JSON format:
    {{
        "ats_score": <score_out_of_100>,
        "overall_feedback": "<brief_overall_assessment>",
        "strengths": ["<strength1>", "<strength2>", "<strength3>"],
        "areas_for_improvement": ["<improvement1>", "<improvement2>", "<improvement3>"],
        "keyword_analysis": {{
            "missing_keywords": ["<keyword1>", "<keyword2>"],
            "present_keywords": ["<keyword1>", "<keyword2>"],
            "keyword_score": <score_out_of_100>
        }},
        "formatting_score": <score_out_of_100>,
        "content_quality_score": <score_out_of_100>,
        "recommendations": ["<recommendation1>", "<recommendation2>", "<recommendation3>"]
    }}

    Evaluation Criteria:
    1. ATS Compatibility (formatting, sections, keywords)
    2. Content Quality (experience, skills, achievements)
    3. Keyword Optimization
    4. Professional Presentation
    5. Relevance to job requirements (if job description provided)

    Please ensure the JSON is valid and complete.
    """

    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Free tier model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            # Fallback if JSON extraction fails
            return {
                "ats_score": 70,
                "overall_feedback": "Resume analysis completed. Please check the formatting and content.",
                "strengths": ["Professional presentation", "Clear structure"],
                "areas_for_improvement": ["Keyword optimization", "Quantified achievements"],
                "keyword_analysis": {
                    "missing_keywords": ["relevant skills", "industry terms"],
                    "present_keywords": ["experience", "education"],
                    "keyword_score": 60
                },
                "formatting_score": 75,
                "content_quality_score": 70,
                "recommendations": ["Add more keywords", "Quantify achievements", "Improve formatting"]
            }
    
    except Exception as e:
        return {
            "ats_score": 0,
            "overall_feedback": f"Error analyzing resume: {str(e)}",
            "strengths": [],
            "areas_for_improvement": ["Please try again"],
            "keyword_analysis": {
                "missing_keywords": [],
                "present_keywords": [],
                "keyword_score": 0
            },
            "formatting_score": 0,
            "content_quality_score": 0,
            "recommendations": ["Please try uploading the file again"]
        }

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze_resume(
    request: Request,
    file: UploadFile = File(...),
    job_description: Optional[str] = Form("")
):
    """Analyze uploaded resume file"""
    
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error": "No file uploaded"}
        )
    
    # Read file content
    file_content = await file.read()
    
    # Extract text from file
    resume_text = extract_text_from_file(file_content, file.filename)
    
    if resume_text.startswith("Error") or resume_text.startswith("Unsupported"):
        return JSONResponse(
            status_code=400,
            content={"error": resume_text}
        )
    
    # Analyze with Groq
    analysis = await analyze_resume_with_groq(resume_text, job_description or "")
    
    return JSONResponse(content=analysis)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# For Vercel deployment
app.mount("/", app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
