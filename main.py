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

    STRICT SCORING METHODOLOGY:
    - 95-100: Exceptional - Perfect ATS optimization, 99%+ interview probability (requires ALL: 15+ quantified achievements, 20+ relevant keywords, perfect formatting, 3+ years relevant experience)
    - 85-94: Excellent - Outstanding candidate, 90%+ ATS pass rate (requires: 10+ quantified achievements, 15+ keywords, excellent formatting, clear progression)
    - 75-84: Very Good - Strong candidate, 75%+ ATS pass rate (requires: 6+ quantified achievements, 12+ keywords, good formatting, relevant experience)
    - 65-74: Good - Above average, 60% ATS pass rate (requires: 3+ quantified achievements, 8+ keywords, decent formatting)
    - 55-64: Fair - Average performance, 40% ATS pass rate (requires: 1+ quantified achievement, 5+ keywords, basic formatting)
    - 45-54: Below Average - Needs improvement, 25% ATS pass rate (missing key elements but has potential)
    - 35-44: Weak - Significant issues, 15% ATS pass rate (major gaps in content or formatting)
    - 25-34: Poor - Major problems, 5% ATS pass rate (fundamental issues throughout)
    - Below 25: Critical - Complete overhaul needed, <1% ATS pass rate (fails basic requirements)

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

    CRITICAL REQUIREMENTS FOR SCORING:
    - Extract keywords dynamically from the provided job description when available
    - Provide job-agnostic analysis when no job description is given
    - Use STRICT scoring criteria - scores above 85 require exceptional quality
    - Focus on measurable, actionable feedback with specific examples
    - Ensure all keywords are relevant to the resume content and target role
    - Score realistically based on actual ATS performance standards and market competition
    - Provide specific, implementable recommendations with clear success metrics
    - Maintain valid JSON format without any additional text

    STRICT SCORING ENFORCEMENT:
    - 95-100: Perfect resume, exceptional across all criteria, top 1% of candidates
    - 85-94: Outstanding quality, minimal improvements needed, top 5% of candidates  
    - 75-84: Strong performance, competitive candidate, top 15% of candidates
    - 65-74: Good foundation, needs optimization, top 30% of candidates
    - 55-64: Average performance, requires improvements, top 50% of candidates
    - Below 55: Needs significant work to be competitive in job market
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
    """Provide comprehensive analysis with strict scoring criteria when Groq API is not available"""
    
    # Dynamic keyword extraction from resume content
    resume_lower = resume_text.lower()
    
    # Extract potential keywords from the resume itself (nouns, technical terms, skills)
    import re
    
    # Find words that appear to be skills or important terms (capitalized words, technical terms)
    potential_keywords = []
    
    # Look for skill-related sections with more precise extraction
    skills_section = re.search(r'(skills?|technical|competencies|expertise|proficienc)(.*?)(?=\n[A-Z]|\n\n|$)', resume_text, re.IGNORECASE | re.DOTALL)
    if skills_section:
        skills_text = skills_section.group(2)
        # Extract comma-separated skills or bulleted skills
        skills_matches = re.findall(r'[A-Za-z][A-Za-z\s\.\+#-]+(?=[,\n•\-\*]|$)', skills_text)
        potential_keywords.extend([skill.strip() for skill in skills_matches if len(skill.strip()) > 2])
    
    # Find technical terms and proper nouns (likely to be technologies, companies, etc.)
    technical_terms = re.findall(r'\b[A-Z][a-z]*[A-Z][A-Za-z]*\b|\b[A-Z]{2,}\b|[A-Za-z]+\+\+?|\b\w*[Tt]ech\w*\b', resume_text)
    potential_keywords.extend(technical_terms)
    
    # Expand action verbs list for more comprehensive detection
    action_verbs_found = re.findall(r'\b(developed?|created?|managed?|led|implemented?|designed?|built|improved?|increased?|reduced?|achieved?|delivered?|coordinated?|supervised?|executed?|optimized?|streamlined?|collaborated?|facilitated?|initiated?|established?|launched|transformed|accelerated|exceeded|generated|pioneered|mentored?|trained|negotiated?|resolved|analyzed|researched|strategized|innovated?|automated|scaled|modernized)\b', resume_lower)
    
    # Clean and deduplicate keywords with stricter criteria
    present_keywords = list(set([kw.strip() for kw in potential_keywords if len(kw.strip()) > 2 and len(kw.strip()) < 30]))[:15]
    action_words = list(set(action_verbs_found))[:10]
    
    # Combine for a comprehensive keyword list
    all_found_keywords = present_keywords + action_words
    
    # STRICT CONTENT ANALYSIS WITH PRECISE SCORING
    word_count = len(resume_text.split())
    sentence_count = len([s for s in resume_text.split('.') if s.strip()])
    paragraph_count = len([p for p in resume_text.split('\n\n') if p.strip()])
    
    # Enhanced content quality indicators with strict requirements
    has_contact = any(indicator in resume_lower for indicator in ["email", "phone", "@", ".com", "linkedin", "github"])
    has_experience = any(indicator in resume_lower for indicator in ["experience", "work", "job", "position", "role", "employment"])
    has_education = any(indicator in resume_lower for indicator in ["education", "degree", "university", "college", "bachelor", "master", "phd"])
    has_skills = any(indicator in resume_lower for indicator in ["skills", "technical", "programming", "software", "competencies", "expertise"])
    has_achievements = len(action_verbs_found) > 5  # Increased threshold
    
    # STRICT QUANTIFIED RESULTS DETECTION
    quantified_results = re.findall(r'\d+%|\$\d+|\d+\+|[0-9,]+\s*(users|customers|projects|team|million|thousand|years?|months?|increase|decrease|growth|reduction|improvement|efficiency)', resume_lower)
    quantified_count = len(quantified_results)
    has_quantified_results = quantified_count >= 3  # Require multiple quantified achievements
    
    # ENHANCED DATE AND CHRONOLOGY DETECTION
    date_patterns = re.findall(r'\b\d{4}\b|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}|(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}', resume_lower)
    has_proper_dates = len(date_patterns) >= 4  # Require multiple dates
    
    # PROFESSIONAL CERTIFICATIONS AND CREDENTIALS
    has_certifications = bool(re.search(r'\b(certified?|certification|license|credential|accredited|diploma)\b', resume_lower))
    
    # LEADERSHIP AND MANAGEMENT INDICATORS
    leadership_terms = re.findall(r'\b(led|managed?|supervised|directed|coordinated|oversaw|mentored|guided|trained|developed team|team lead|project manager|senior|principal|head of|director|vp|vice president)\b', resume_lower)
    has_leadership = len(leadership_terms) >= 3
    
    # ADVANCED FORMATTING ANALYSIS WITH STRICT CRITERIA
    has_proper_sections = len(re.findall(r'\n\s*[A-Z][A-Z\s]{2,20}:?\s*\n', resume_text)) >= 4  # Require more sections
    has_bullet_points = resume_text.count('•') > 5 or resume_text.count('\n-') > 8 or resume_text.count('\n*') > 8  # Higher requirements
    consistent_formatting = len(re.findall(r'\n[A-Z][a-z]+:', resume_text)) >= 3
    proper_length = 200 <= word_count <= 800  # Strict word count range
    
    # STRICT SCORING ALGORITHM - START WITH 0 AND EARN POINTS
    score = 0
    
    # CORE REQUIREMENTS (Maximum 40 points) - Must have these basics
    if has_contact: score += 8
    if has_experience: score += 12
    if has_education: score += 8
    if has_skills: score += 12
    
    # CONTENT QUALITY (Maximum 35 points)
    if word_count > 200: score += 5
    if word_count > 400: score += 5
    if proper_length: score += 10  # Bonus for optimal length
    if quantified_count >= 1: score += 5
    if quantified_count >= 3: score += 10  # Significant bonus for multiple metrics
    if quantified_count >= 6: score += 5   # Extra bonus for exceptional metrics
    
    # PROFESSIONAL PRESENTATION (Maximum 25 points)
    if has_achievements: score += 8
    if has_leadership: score += 7
    if has_certifications: score += 5
    if has_proper_dates: score += 5
    
    # KEYWORD OPTIMIZATION - STRICT CALCULATION
    keyword_count = len(all_found_keywords)
    if keyword_count >= 5: score += 3
    if keyword_count >= 8: score += 4
    if keyword_count >= 12: score += 6
    if keyword_count >= 15: score += 7
    if keyword_count >= 20: score += 5  # Excellence bonus
    
    # FORMATTING EXCELLENCE (Maximum deduction/bonus approach)
    formatting_bonus = 0
    if has_proper_sections: formatting_bonus += 8
    if has_bullet_points: formatting_bonus += 7
    if consistent_formatting: formatting_bonus += 5
    score += formatting_bonus
    
    # PENALTY SYSTEM FOR CRITICAL ISSUES
    if word_count < 150: score -= 15  # Too short penalty
    if word_count > 1000: score -= 10  # Too long penalty
    if not has_achievements: score -= 8  # Lack of action verbs
    if quantified_count == 0: score -= 12  # No quantified results penalty
    
    # Ensure score is within 0-100 range
    score = max(0, min(100, score))
    
    # COMPONENT SCORES WITH STRICT CRITERIA
    keyword_score = min(100, (keyword_count / 15) * 100)  # Based on 15 keywords as excellent
    
    formatting_score = 20  # Start low
    if has_proper_sections: formatting_score += 25
    if has_bullet_points: formatting_score += 25
    if consistent_formatting: formatting_score += 20
    if proper_length: formatting_score += 10
    
    content_score = 15  # Start low
    if has_achievements: content_score += 15
    if has_quantified_results: content_score += 25
    if has_leadership: content_score += 15
    if has_certifications: content_score += 10
    if has_proper_dates: content_score += 10
    if sentence_count > 15: content_score += 10
    
    # Ensure all component scores are within range
    keyword_score = max(0, min(100, int(keyword_score)))
    formatting_score = max(0, min(100, int(formatting_score)))
    content_score = max(0, min(100, int(content_score)))
    
    # STRICT GRADE BOUNDARIES
    if score >= 95:
        grade = "Exceptional"
        feedback_level = "outstanding"
    elif score >= 85:
        grade = "Excellent"
        feedback_level = "excellent"
    elif score >= 75:
        grade = "Very Good"
        feedback_level = "strong"
    elif score >= 65:
        grade = "Good"
        feedback_level = "good"
    elif score >= 55:
        grade = "Fair"
        feedback_level = "moderate"
    elif score >= 45:
        grade = "Below Average"
        feedback_level = "below average"
    elif score >= 35:
        grade = "Weak"
        feedback_level = "weak"
    elif score >= 25:
        grade = "Poor"
        feedback_level = "poor"
    else:
        grade = "Critical"
        feedback_level = "critical"
    
    # Generate dynamic feedback based on strict analysis
    strengths = []
    if quantified_count >= 3:
        strengths.append("Contains multiple quantified achievements demonstrating measurable impact")
    elif quantified_count >= 1:
        strengths.append("Includes some quantified achievements showing results")
    
    if len(all_found_keywords) >= 12:
        strengths.append("Rich keyword content with comprehensive professional terminology")
    elif len(all_found_keywords) >= 8:
        strengths.append("Good keyword usage with relevant professional terms")
    
    if has_proper_sections and has_bullet_points:
        strengths.append("Excellent ATS-friendly formatting with clear structure")
    elif has_proper_sections or has_bullet_points:
        strengths.append("Well-organized structure with clear sections")
    
    if has_leadership:
        strengths.append("Demonstrates leadership experience and management capabilities")
    elif has_achievements:
        strengths.append("Uses strong action verbs to describe professional accomplishments")
    
    if has_certifications:
        strengths.append("Professional certifications enhance credibility and expertise")
    
    # Ensure we have at least 4 strengths
    additional_strengths = [
        "Professional file format compatible with ATS systems",
        "Contains comprehensive contact information" if has_contact else "Resume format successfully processed",
        "Demonstrates relevant work experience progression" if has_experience else "Content structure shows professional presentation",
        "Educational background clearly documented" if has_education else "Clear information hierarchy maintained"
    ]
    while len(strengths) < 4:
        for strength in additional_strengths:
            if len(strengths) < 4 and strength not in strengths:
                strengths.append(strength)
    
    # Generate improvement areas based on strict requirements
    improvements = []
    if quantified_count < 3:
        improvements.append("Add more quantified achievements with specific metrics, percentages, and measurable results")
    if len(all_found_keywords) < 12:
        improvements.append("Incorporate additional industry-relevant keywords and technical terminology")
    if not (has_proper_sections and has_bullet_points):
        improvements.append("Improve document formatting with consistent sections and bullet points")
    if not has_leadership and len(leadership_terms) < 2:
        improvements.append("Highlight leadership experience and management responsibilities more prominently")
    if not has_certifications:
        improvements.append("Consider adding relevant certifications or professional credentials")
    if word_count < 300:
        improvements.append("Expand content to provide more comprehensive career details and achievements")
    
    # Fill remaining improvement slots
    general_improvements = [
        "Optimize keyword density for better ATS ranking",
        "Ensure chronological consistency throughout work history",
        "Align skills section more precisely with target job requirements",
        "Enhance professional summary with stronger value proposition"
    ]
    while len(improvements) < 4:
        for improvement in general_improvements:
            if len(improvements) < 4 and improvement not in improvements:
                improvements.append(improvement)
    
    # Generate strict recommendations
    recommendations = [
        "Research target job descriptions and incorporate specific required keywords",
        "Quantify ALL achievements with numbers, percentages, dollar amounts, or timeframes",
        "Use consistent ATS-friendly formatting with clear sections and bullet points",
        "Tailor resume content to match each specific job application",
        "Ensure optimal length (300-600 words) with rich, relevant content"
    ]
    
    # Generate missing keywords as specific actionable categories
    missing_keyword_categories = [
        "role-specific technical skills",
        "industry certifications",
        "management/leadership terms",
        "quantitative metrics",
        "software/tools proficiency"
    ]

    return {
        "ats_score": score,
        "overall_feedback": f"Your resume receives a {grade} rating with a strict ATS score of {score}/100. {feedback_level.title()} performance indicates {'excellent ATS compatibility with high interview probability' if score >= 85 else 'strong foundation requiring targeted optimizations' if score >= 65 else 'significant improvements needed for competitive ranking'}. Focus on {'maintaining excellence' if score >= 85 else 'keyword optimization and quantified achievements' if score >= 65 else 'comprehensive content enhancement and formatting improvements'}.",
        "strengths": strengths,
        "areas_for_improvement": improvements,
        "keyword_analysis": {
            "missing_keywords": missing_keyword_categories,
            "present_keywords": all_found_keywords if all_found_keywords else ["basic professional terms found"],
            "keyword_score": keyword_score
        },
        "formatting_score": formatting_score,
        "content_quality_score": content_score,
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
