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
       - Extract keywords directly from the job description (if provided) and compare with resume
       - Identify technical terms, skills, and qualifications mentioned in resume
       - Analyze action verbs and power words usage
       - Evaluate industry-relevant terminology presence
       - Check for job title variations and role-specific language
       - Assess professional certifications and qualifications alignment

    2. FORMATTING & STRUCTURE ANALYSIS (25% weight):
       - ATS-friendly formatting (no tables, graphics, complex layouts)
       - Clear section headers (Experience, Education, Skills, Contact, etc.)
       - Consistent date formatting and chronological order
       - Proper use of bullet points vs. paragraphs
       - Professional font usage and readability
       - File format compatibility and parsing ease

    3. CONTENT QUALITY & RELEVANCE (25% weight):
       - Quantified achievements with specific metrics and results
       - Relevant work experience progression and career growth
       - Education and certification alignment with role requirements
       - Skills currency and relevance to target position
       - Industry experience depth and breadth
       - Career gap identification and impact assessment

    4. PROFESSIONAL PRESENTATION (20% weight):
       - Complete contact information (email, phone, location)
       - Professional summary or objective effectiveness
       - Chronological consistency and logical flow
       - Grammar, spelling, and language quality
       - Appropriate resume length for experience level
       - Overall professional tone and presentation

    SCORING METHODOLOGY:
    - 90-100: Exceptional - Top 5% of candidates, will likely pass all ATS filters and secure interviews
    - 80-89: Strong - Top 15% of candidates, high probability of passing ATS screening
    - 70-79: Good - Above average, needs minor optimizations to improve ranking
    - 60-69: Fair - Average performance, requires targeted improvements for better results
    - 50-59: Weak - Below average, needs significant revisions to be competitive
    - Below 50: Poor - Major improvements needed, unlikely to pass initial ATS screening

    INSTRUCTIONS FOR KEYWORD ANALYSIS:
    - If job description is provided, extract specific keywords from it and match against resume
    - If no job description provided, identify professional terms, skills, and industry language from resume
    - Focus on role-relevant keywords rather than generic terms
    - Suggest missing keywords based on industry standards and common requirements
    - Evaluate keyword density and natural integration

    Provide your analysis in this EXACT JSON format (ensure valid JSON syntax):
    {{
        "ats_score": <integer_0_to_100>,
        "overall_feedback": "<comprehensive_2-3_sentence_assessment_with_specific_insights>",
        "strengths": [
            "<specific_strength_with_actionable_context>",
            "<specific_strength_with_actionable_context>",
            "<specific_strength_with_actionable_context>",
            "<specific_strength_with_actionable_context>"
        ],
        "areas_for_improvement": [
            "<specific_actionable_improvement_with_clear_guidance>",
            "<specific_actionable_improvement_with_clear_guidance>",
            "<specific_actionable_improvement_with_clear_guidance>",
            "<specific_actionable_improvement_with_clear_guidance>"
        ],
        "keyword_analysis": {{
            "missing_keywords": [
                "<important_missing_keyword_relevant_to_role>",
                "<important_missing_keyword_relevant_to_role>",
                "<important_missing_keyword_relevant_to_role>",
                "<important_missing_keyword_relevant_to_role>",
                "<important_missing_keyword_relevant_to_role>"
            ],
            "present_keywords": [
                "<relevant_keyword_found_in_resume>",
                "<relevant_keyword_found_in_resume>",
                "<relevant_keyword_found_in_resume>",
                "<relevant_keyword_found_in_resume>",
                "<relevant_keyword_found_in_resume>"
            ],
            "keyword_score": <integer_0_to_100>
        }},
        "formatting_score": <integer_0_to_100>,
        "content_quality_score": <integer_0_to_100>,
        "recommendations": [
            "<specific_actionable_recommendation_with_clear_steps>",
            "<specific_actionable_recommendation_with_clear_steps>",
            "<specific_actionable_recommendation_with_clear_steps>",
            "<specific_actionable_recommendation_with_clear_steps>",
            "<specific_actionable_recommendation_with_clear_steps>"
        ]
    }}

    CRITICAL REQUIREMENTS:
    - Extract keywords dynamically from the provided job description when available
    - Provide job-agnostic analysis when no job description is given
    - Focus on measurable, actionable feedback
    - Ensure all keywords are relevant to the resume content and target role
    - Score realistically based on actual ATS performance standards
    - Provide specific, implementable recommendations
    - Maintain valid JSON format without any additional text
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
    
    # Dynamic keyword extraction from resume content
    resume_lower = resume_text.lower()
    
    # Extract potential keywords from the resume itself (nouns, technical terms, skills)
    import re
    
    # Find words that appear to be skills or important terms (capitalized words, technical terms)
    potential_keywords = []
    
    # Look for skill-related sections
    skills_section = re.search(r'(skills?|technical|competencies|expertise|proficienc)(.*?)(?=\n[A-Z]|\n\n|$)', resume_text, re.IGNORECASE | re.DOTALL)
    if skills_section:
        skills_text = skills_section.group(2)
        # Extract comma-separated skills or bulleted skills
        skills_matches = re.findall(r'[A-Za-z][A-Za-z\s\.\+#-]+(?=[,\n•\-\*]|$)', skills_text)
        potential_keywords.extend([skill.strip() for skill in skills_matches if len(skill.strip()) > 2])
    
    # Find technical terms and proper nouns (likely to be technologies, companies, etc.)
    technical_terms = re.findall(r'\b[A-Z][a-z]*[A-Z][A-Za-z]*\b|\b[A-Z]{2,}\b|[A-Za-z]+\+\+?|\b\w*[Tt]ech\w*\b', resume_text)
    potential_keywords.extend(technical_terms)
    
    # Find action verbs and power words commonly used in resumes
    action_verbs_found = re.findall(r'\b(developed?|created?|managed?|led|implemented?|designed?|built|improved?|increased?|reduced?|achieved?|delivered?|coordinated?|supervised?|executed?|optimized?|streamlined?|collaborated?|facilitated?|initiated?|established?)\b', resume_lower)
    
    # Clean and deduplicate keywords
    present_keywords = list(set([kw.strip() for kw in potential_keywords if len(kw.strip()) > 2 and len(kw.strip()) < 25]))[:10]
    action_words = list(set(action_verbs_found))[:5]
    
    # Combine for a comprehensive keyword list
    all_found_keywords = present_keywords + action_words
    
    # Advanced content analysis
    word_count = len(resume_text.split())
    sentence_count = len([s for s in resume_text.split('.') if s.strip()])
    paragraph_count = len([p for p in resume_text.split('\n\n') if p.strip()])
    
    # Check for key sections and content quality indicators
    has_contact = any(indicator in resume_lower for indicator in ["email", "phone", "@", ".com", "linkedin", "github"])
    has_experience = any(indicator in resume_lower for indicator in ["experience", "work", "job", "position", "role", "employment"])
    has_education = any(indicator in resume_lower for indicator in ["education", "degree", "university", "college", "bachelor", "master", "phd"])
    has_skills = any(indicator in resume_lower for indicator in ["skills", "technical", "programming", "software", "competencies", "expertise"])
    has_achievements = len(action_verbs_found) > 3
    has_quantified_results = bool(re.search(r'\d+%|\$\d+|\d+\+|[0-9,]+\s*(users|customers|projects|team|million|thousand|years?|months?)', resume_lower))
    has_dates = bool(re.search(r'\b\d{4}\b|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', resume_lower))
    
    # Formatting analysis
    has_proper_sections = len(re.findall(r'\n\s*[A-Z][A-Z\s]{2,20}:?\s*\n', resume_text)) >= 3
    has_bullet_points = resume_text.count('•') > 2 or resume_text.count('\n-') > 3 or resume_text.count('\n*') > 3
    consistent_formatting = len(re.findall(r'\n[A-Z][a-z]+:', resume_text)) >= 2
    
    # Calculate sophisticated scores
    base_score = 45
    
    # Content scoring (40 points max)
    if word_count > 150: base_score += 4
    if word_count > 300: base_score += 4
    if word_count > 500: base_score += 4
    if has_contact: base_score += 8
    if has_experience: base_score += 10
    if has_education: base_score += 6
    if has_skills: base_score += 8
    if has_achievements: base_score += 8
    if has_quantified_results: base_score += 12
    if has_dates: base_score += 4
    if paragraph_count > 5: base_score += 3
    
    # Keyword scoring based on content richness
    keyword_density = min(len(all_found_keywords) / max(10, word_count/50), 1.0)  # Dynamic based on content length
    keyword_score = min(100, keyword_density * 100 + 30)
    
    # Formatting scoring
    formatting_score = 55
    if has_proper_sections: formatting_score += 20
    if has_bullet_points: formatting_score += 15
    if consistent_formatting: formatting_score += 10
    
    # Content quality scoring
    content_score = base_score + 5
    if sentence_count > 10: content_score += 5
    if len(all_found_keywords) > 8: content_score += 8
    if has_quantified_results: content_score += 10
    
    # Final ATS score calculation
    final_score = min(100, int((base_score * 0.4) + (keyword_score * 0.3) + (formatting_score * 0.2) + (content_score * 0.1)))
    
    # Generate dynamic feedback based on analysis
    strengths = []
    if has_quantified_results:
        strengths.append("Contains quantified achievements that demonstrate measurable impact")
    if len(all_found_keywords) > 8:
        strengths.append("Rich content with relevant professional terminology")
    if has_proper_sections:
        strengths.append("Well-organized structure with clear section divisions")
    if word_count > 400:
        strengths.append("Comprehensive content provides detailed professional background")
    if has_achievements:
        strengths.append("Uses strong action verbs to describe accomplishments")
    
    # Fill remaining strength slots with dynamic analysis
    additional_strengths = [
        "Professional file format compatible with ATS systems",
        "Contains essential contact information" if has_contact else "Resume format successfully processed",
        "Demonstrates relevant work experience" if has_experience else "Content structure shows professional presentation",
        "Educational background clearly presented" if has_education else "Clear information hierarchy maintained"
    ]
    while len(strengths) < 4:
        for strength in additional_strengths:
            if len(strengths) < 4 and strength not in strengths:
                strengths.append(strength)
    
    # Generate improvement areas based on what's missing
    improvements = []
    if not has_quantified_results:
        improvements.append("Add quantified achievements with specific numbers, percentages, or metrics")
    if len(all_found_keywords) < 6:
        improvements.append("Incorporate more industry-relevant keywords and technical terminology")
    if not has_proper_sections:
        improvements.append("Improve document structure with clear section headers")
    if word_count < 250:
        improvements.append("Expand content to provide more comprehensive career details")
    if not has_achievements:
        improvements.append("Use stronger action verbs to highlight accomplishments")
    
    # Fill remaining improvement slots with general best practices
    general_improvements = [
        "Tailor keyword usage to match specific job requirements",
        "Ensure consistent formatting throughout the document",
        "Optimize content length for your experience level",
        "Align skills section with target job requirements",
        "Review for ATS-friendly formatting guidelines"
    ]
    while len(improvements) < 4:
        for improvement in general_improvements:
            if len(improvements) < 4 and improvement not in improvements:
                improvements.append(improvement)
    
    # Generate recommendations that are always relevant
    recommendations = [
        "Research and include keywords from your target job descriptions",
        "Quantify your achievements with specific numbers and results",
        "Ensure consistent formatting with clear section headers and bullet points",
        "Tailor your resume content to match each job application",
        "Use a standard, ATS-friendly resume format without complex graphics"
    ]
    
    # Generate missing keywords as general categories rather than specific terms
    missing_keyword_categories = [
        "industry-specific terms",
        "technical skills",
        "soft skills",
        "certifications",
        "methodologies"
    ]
    
    return {
        "ats_score": final_score,
        "overall_feedback": f"Your resume shows {'strong' if final_score > 75 else 'good' if final_score > 60 else 'moderate'} ATS compatibility with a score of {final_score}/100. {'Focus on keyword optimization and quantified achievements to reach the next level.' if final_score < 80 else 'Great foundation - minor optimizations will significantly improve your ranking.'}",
        "strengths": strengths,
        "areas_for_improvement": improvements,
        "keyword_analysis": {
            "missing_keywords": missing_keyword_categories,  # Generic categories instead of specific terms
            "present_keywords": all_found_keywords if all_found_keywords else ["professional terms found in content"],
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
