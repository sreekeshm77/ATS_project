import os
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import PyPDF2
import docx
import io
import json
import re
import requests
from typing import Optional
from dotenv import load_dotenv

# Try to import Groq, fallback to direct API calls if it fails
try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    GROQ_SDK_AVAILABLE = False
    print("Groq SDK not available, using direct API calls")

# Load environment variables
load_dotenv()

app = FastAPI(title="ATS Resume Checker", description="AI-powered ATS score checker for resumes")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize Groq client with proper error handling for serverless
def get_groq_client():
    """Initialize Groq client with proper error handling"""
    if not GROQ_SDK_AVAILABLE:
        return None
        
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Warning: GROQ_API_KEY not found in environment variables")
            return None
        return Groq(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return None

def groq_direct_api(prompt, api_key):
    """Direct API call to Groq without using the SDK"""
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Direct API request failed: {e}")
        return None

# Global variable for Groq client
groq_client = None

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
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return get_fallback_analysis(resume_text)
    
    prompt = f"""
    As an expert ATS (Applicant Tracking System) analyzer, please analyze the following resume and provide a comprehensive evaluation.

    Resume Content:
    {resume_text[:3000]}  

    Job Description (if provided):
    {job_description[:1000]}

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

    # Try SDK first, then direct API
    content = None
    
    if GROQ_SDK_AVAILABLE:
        try:
            global groq_client
            if groq_client is None:
                groq_client = get_groq_client()
            
            if groq_client is not None:
                response = groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000
                )
                content = response.choices[0].message.content
        except Exception as e:
            print(f"Groq SDK failed: {e}")
            content = None
    
    # If SDK failed, try direct API
    if content is None:
        content = groq_direct_api(prompt, api_key)
    
    # Process the response
    if content:
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return result
        except Exception as e:
            print(f"Error parsing AI response: {e}")
    
    # Fallback if everything fails
    return get_fallback_analysis(resume_text)

def get_fallback_analysis(resume_text: str) -> dict:
    """Provide basic analysis when Groq API is not available"""
    
    # Basic keyword analysis
    common_keywords = ["experience", "skills", "education", "work", "project", "management", "development", "team", "leadership", "communication"]
    present_keywords = [keyword for keyword in common_keywords if keyword.lower() in resume_text.lower()]
    missing_keywords = [keyword for keyword in common_keywords if keyword.lower() not in resume_text.lower()]
    
    # Basic scoring based on content length and structure
    word_count = len(resume_text.split())
    has_contact = any(indicator in resume_text.lower() for indicator in ["email", "phone", "@", ".com"])
    has_experience = any(indicator in resume_text.lower() for indicator in ["experience", "work", "job", "position"])
    has_education = any(indicator in resume_text.lower() for indicator in ["education", "degree", "university", "college"])
    has_skills = any(indicator in resume_text.lower() for indicator in ["skills", "technical", "programming", "software"])
    
    # Calculate scores
    base_score = 60
    if word_count > 200: base_score += 10
    if has_contact: base_score += 5
    if has_experience: base_score += 10
    if has_education: base_score += 5
    if has_skills: base_score += 10
    
    keyword_score = min(100, (len(present_keywords) / len(common_keywords)) * 100)
    formatting_score = min(100, base_score + 5)
    content_score = min(100, base_score)
    
    return {
        "ats_score": min(100, base_score),
        "overall_feedback": "Resume analysis completed using basic evaluation. For advanced AI insights, please check your API configuration.",
        "strengths": [
            "Resume uploaded successfully",
            "Content appears structured" if word_count > 100 else "File processed successfully",
            "Contains relevant sections" if has_experience else "Basic information present"
        ],
        "areas_for_improvement": [
            "Add more industry-specific keywords" if len(present_keywords) < 5 else "Enhance keyword density",
            "Include quantified achievements",
            "Ensure ATS-friendly formatting"
        ],
        "keyword_analysis": {
            "missing_keywords": missing_keywords[:5],  # Show up to 5
            "present_keywords": present_keywords[:10],  # Show up to 10
            "keyword_score": int(keyword_score)
        },
        "formatting_score": int(formatting_score),
        "content_quality_score": int(content_score),
        "recommendations": [
            "Add more specific technical skills",
            "Include quantified achievements with numbers",
            "Use standard resume sections (Experience, Education, Skills)",
            "Optimize for applicant tracking systems"
        ]
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
