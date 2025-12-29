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
    You are a senior HR manager and ATS (Applicant Tracking System) expert with 15+ years of experience in talent acquisition across Fortune 500 companies. You have deep expertise in how ATS systems parse, score, and rank resumes. Your analysis has helped thousands of candidates secure interviews at top-tier companies.

    RESUME TO ANALYZE:
    {resume_text[:4000]}

    JOB DESCRIPTION (if provided):
    {job_description[:1500]}

    COMPREHENSIVE ATS ANALYSIS FRAMEWORK:

    1. KEYWORD OPTIMIZATION ANALYSIS (30% weight):
       - Industry-specific technical keywords
       - Action verbs and power words
       - Skills matching (hard and soft skills)
       - Job title variations and synonyms
       - Certification and qualification keywords
       - Location and availability keywords

    2. FORMATTING & STRUCTURE ANALYSIS (25% weight):
       - ATS-friendly formatting (no tables, graphics, headers/footers)
       - Proper section headers (Experience, Education, Skills, etc.)
       - Consistent date formatting
       - Bullet points vs. paragraphs
       - Font compatibility and readability
       - File format compatibility

    3. CONTENT QUALITY & RELEVANCE (25% weight):
       - Quantified achievements with metrics
       - Relevant work experience progression
       - Education alignment with role
       - Skills relevance and currency
       - Industry experience match
       - Career gap analysis

    4. PROFESSIONAL PRESENTATION (20% weight):
       - Contact information completeness
       - Professional summary effectiveness
       - Chronological consistency
       - Grammar and spelling accuracy
       - Length appropriateness
       - Overall professional tone

    DETAILED SCORING METHODOLOGY:
    - 90-100: Exceptional - Top 5% of candidates, likely to pass all ATS filters
    - 80-89: Strong - Top 15% of candidates, high interview probability
    - 70-79: Good - Above average, needs minor optimizations
    - 60-69: Fair - Average candidate, requires significant improvements
    - 50-59: Weak - Below average, major revisions needed
    - Below 50: Poor - Unlikely to pass ATS screening

    Provide your analysis in this EXACT JSON format (ensure valid JSON syntax):
    {{
        "ats_score": <integer_0_to_100>,
        "overall_feedback": "<2-3_sentence_comprehensive_assessment>",
        "strengths": [
            "<specific_strength_with_context>",
            "<specific_strength_with_context>",
            "<specific_strength_with_context>",
            "<specific_strength_with_context>"
        ],
        "areas_for_improvement": [
            "<specific_actionable_improvement>",
            "<specific_actionable_improvement>",
            "<specific_actionable_improvement>",
            "<specific_actionable_improvement>"
        ],
        "keyword_analysis": {{
            "missing_keywords": [
                "<critical_missing_keyword>",
                "<critical_missing_keyword>",
                "<critical_missing_keyword>",
                "<critical_missing_keyword>",
                "<critical_missing_keyword>"
            ],
            "present_keywords": [
                "<found_relevant_keyword>",
                "<found_relevant_keyword>",
                "<found_relevant_keyword>",
                "<found_relevant_keyword>",
                "<found_relevant_keyword>"
            ],
            "keyword_score": <integer_0_to_100>
        }},
        "formatting_score": <integer_0_to_100>,
        "content_quality_score": <integer_0_to_100>,
        "recommendations": [
            "<specific_actionable_recommendation>",
            "<specific_actionable_recommendation>",
            "<specific_actionable_recommendation>",
            "<specific_actionable_recommendation>",
            "<specific_actionable_recommendation>"
        ]
    }}

    CRITICAL INSTRUCTIONS:
    - Be extremely thorough and specific in your analysis
    - Focus on actionable, concrete feedback
    - Consider industry standards and current job market trends
    - Identify specific keywords that would improve ATS ranking
    - Provide realistic scores based on actual ATS performance expectations
    - Ensure all JSON values are properly formatted strings or integers
    - Do not include any text outside the JSON response
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
    """Provide comprehensive analysis when Groq API is not available"""
    
    # Enhanced keyword analysis with industry-specific terms
    technical_keywords = ["programming", "development", "software", "coding", "algorithm", "database", "framework", "api", "cloud", "devops", "ci/cd", "agile", "scrum"]
    business_keywords = ["management", "leadership", "strategy", "analysis", "optimization", "project", "team", "collaboration", "communication", "planning"]
    soft_skills = ["problem-solving", "critical thinking", "creativity", "adaptability", "time management", "attention to detail", "multitasking"]
    
    all_keywords = technical_keywords + business_keywords + soft_skills
    present_keywords = []
    missing_keywords = []
    
    resume_lower = resume_text.lower()
    
    for keyword in all_keywords:
        if keyword.lower() in resume_lower or any(variant in resume_lower for variant in [keyword.replace("-", " "), keyword.replace(" ", "-")]):
            present_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    # Advanced content analysis
    word_count = len(resume_text.split())
    sentence_count = len([s for s in resume_text.split('.') if s.strip()])
    
    # Check for key sections
    has_contact = any(indicator in resume_lower for indicator in ["email", "phone", "@", ".com", "linkedin", "github"])
    has_experience = any(indicator in resume_lower for indicator in ["experience", "work", "job", "position", "role", "employment"])
    has_education = any(indicator in resume_lower for indicator in ["education", "degree", "university", "college", "bachelor", "master", "phd"])
    has_skills = any(indicator in resume_lower for indicator in ["skills", "technical", "programming", "software", "competencies", "expertise"])
    has_achievements = any(indicator in resume_lower for indicator in ["achieved", "improved", "increased", "reduced", "led", "managed", "developed", "created"])
    has_quantified_results = bool(re.search(r'\d+%|\$\d+|\d+\+|[0-9,]+\s*(users|customers|projects|team|million|thousand)', resume_lower))
    
    # Formatting analysis
    has_proper_sections = len(re.findall(r'\n[A-Z][A-Z\s]{2,20}\n', resume_text)) >= 3
    has_bullet_points = '•' in resume_text or resume_text.count('\n- ') > 3 or resume_text.count('\n* ') > 3
    consistent_formatting = not bool(re.search(r'[a-z]\s+[A-Z][a-z]', resume_text))  # Mixed case inconsistencies
    
    # Calculate sophisticated scores
    base_score = 45
    
    # Content scoring (40 points max)
    if word_count > 150: base_score += 5
    if word_count > 300: base_score += 5
    if word_count > 500: base_score += 5
    if has_contact: base_score += 8
    if has_experience: base_score += 12
    if has_education: base_score += 6
    if has_skills: base_score += 8
    if has_achievements: base_score += 10
    if has_quantified_results: base_score += 15
    
    # Keyword scoring
    keyword_density = len(present_keywords) / len(all_keywords)
    keyword_score = min(100, keyword_density * 100 + 20)
    
    # Formatting scoring
    formatting_score = 60
    if has_proper_sections: formatting_score += 15
    if has_bullet_points: formatting_score += 15
    if consistent_formatting: formatting_score += 10
    
    # Content quality scoring
    content_score = base_score
    if sentence_count > 10: content_score += 5
    if len(present_keywords) > 10: content_score += 10
    
    # Final ATS score calculation
    final_score = min(100, int((base_score * 0.4) + (keyword_score * 0.3) + (formatting_score * 0.2) + (content_score * 0.1)))
    
    # Generate dynamic feedback based on analysis
    strengths = []
    if has_quantified_results:
        strengths.append("Contains quantified achievements that demonstrate impact")
    if len(present_keywords) > 15:
        strengths.append("Rich keyword density shows relevant experience")
    if has_proper_sections:
        strengths.append("Well-structured with clear section organization")
    if word_count > 400:
        strengths.append("Comprehensive content provides detailed background")
    
    # Fill remaining strength slots
    default_strengths = [
        "Professional file format is ATS-compatible",
        "Resume successfully parsed and analyzed",
        "Contains relevant industry terminology",
        "Demonstrates career progression and growth"
    ]
    while len(strengths) < 4:
        strengths.append(default_strengths[len(strengths)])
    
    # Generate improvement areas
    improvements = []
    if not has_quantified_results:
        improvements.append("Add quantified achievements with specific numbers, percentages, or metrics")
    if len(present_keywords) < 10:
        improvements.append("Incorporate more industry-specific keywords and technical terminology")
    if not has_proper_sections:
        improvements.append("Improve section organization with clear headers (Experience, Education, Skills)")
    if word_count < 300:
        improvements.append("Expand content to provide more comprehensive career details")
    
    # Fill remaining improvement slots
    default_improvements = [
        "Optimize keyword density for better ATS matching",
        "Enhance formatting consistency throughout the document",
        "Strengthen action verbs and power words usage",
        "Improve alignment with current industry standards"
    ]
    while len(improvements) < 4:
        improvements.append(default_improvements[len(improvements)])
    
    # Generate recommendations
    recommendations = [
        "Use industry-specific keywords that match your target job descriptions",
        "Quantify all achievements with specific numbers, percentages, or dollar amounts",
        "Ensure consistent formatting with proper bullet points and section headers",
        "Tailor your resume content to match the specific job requirements",
        "Include relevant certifications and technical skills prominently"
    ]
    
    return {
        "ats_score": final_score,
        "overall_feedback": f"Your resume shows {'strong' if final_score > 75 else 'good' if final_score > 60 else 'moderate'} ATS compatibility with a score of {final_score}/100. {'Focus on keyword optimization and quantified achievements to reach the next level.' if final_score < 80 else 'Great foundation - minor optimizations will significantly improve your ranking.'}",
        "strengths": strengths,
        "areas_for_improvement": improvements,
        "keyword_analysis": {
            "missing_keywords": missing_keywords[:5],
            "present_keywords": present_keywords[:10] if present_keywords else ["experience", "skills", "work"],
            "keyword_score": int(keyword_score)
        },
        "formatting_score": min(100, formatting_score),
        "content_quality_score": min(100, content_score),
        "recommendations": recommendations
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
