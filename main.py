"""
ATS Pro Resume Analyzer
By Sreekesh M
AI-powered ATS score checker with hybrid analysis
"""

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
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv
import math

# Try to import Groq, fallback to direct API calls if it fails
try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    GROQ_SDK_AVAILABLE = False
    print("Groq SDK not available, using direct API calls")

# Load environment variables
load_dotenv()

app = FastAPI(title="ATS Pro Resume Analyzer", description="AI-powered ATS score checker with hybrid analysis")

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
        "max_tokens": 2500
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=45)
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
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
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

# ============================================
# COMPREHENSIVE DETERMINISTIC ATS ANALYZER
# ============================================

class DeterministicATSAnalyzer:
    """
    Advanced deterministic ATS analyzer with 40+ evaluation criteria
    """
    
    # Industry-specific keyword dictionaries
    TECH_KEYWORDS = {
        'languages': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust', 'php', 'swift', 'kotlin', 'scala', 'sql', 'r', 'matlab'],
        'frameworks': ['react', 'angular', 'vue', 'node', 'django', 'flask', 'spring', 'express', 'rails', 'laravel', 'nextjs', 'gatsby', 'svelte'],
        'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd', 'devops'],
        'data': ['machine learning', 'deep learning', 'data science', 'analytics', 'big data', 'hadoop', 'spark', 'tensorflow', 'pytorch', 'pandas', 'numpy'],
        'tools': ['git', 'github', 'gitlab', 'jira', 'confluence', 'slack', 'figma', 'sketch', 'postman', 'mongodb', 'postgresql', 'mysql', 'redis']
    }
    
    BUSINESS_KEYWORDS = {
        'management': ['project management', 'team lead', 'stakeholder', 'budget', 'strategy', 'planning', 'coordination', 'leadership'],
        'analysis': ['business analysis', 'requirements', 'process improvement', 'data analysis', 'reporting', 'metrics', 'kpi'],
        'communication': ['presentation', 'negotiation', 'client relations', 'cross-functional', 'collaboration'],
        'methodologies': ['agile', 'scrum', 'waterfall', 'lean', 'six sigma', 'kanban', 'pmp', 'prince2']
    }
    
    # Power action verbs with impact weights
    ACTION_VERBS = {
        'high_impact': ['achieved', 'accelerated', 'delivered', 'exceeded', 'generated', 'increased', 'launched', 'led', 'optimized', 'pioneered', 'reduced', 'saved', 'spearheaded', 'streamlined', 'transformed'],
        'medium_impact': ['analyzed', 'built', 'collaborated', 'coordinated', 'created', 'designed', 'developed', 'established', 'implemented', 'improved', 'managed', 'organized', 'produced'],
        'standard': ['assisted', 'conducted', 'contributed', 'executed', 'facilitated', 'handled', 'maintained', 'participated', 'performed', 'prepared', 'processed', 'provided', 'supported']
    }
    
    # Required resume sections
    ESSENTIAL_SECTIONS = ['contact', 'experience', 'education', 'skills']
    RECOMMENDED_SECTIONS = ['summary', 'projects', 'certifications', 'achievements', 'awards']
    
    def __init__(self, resume_text: str, job_description: str = ""):
        self.resume_text = resume_text
        self.resume_lower = resume_text.lower()
        self.job_description = job_description
        self.job_desc_lower = job_description.lower() if job_description else ""
        self.metrics = {}
        self.scores = {}
        
    def analyze(self) -> Dict:
        """Run comprehensive analysis and return results"""
        
        # 1. Basic Document Metrics
        self._analyze_document_metrics()
        
        # 2. Contact Information Analysis
        contact_score = self._analyze_contact_info()
        
        # 3. Section Structure Analysis
        structure_score = self._analyze_structure()
        
        # 4. Keyword Analysis (Technical & Industry)
        keyword_analysis = self._analyze_keywords()
        
        # 5. Quantified Achievements Analysis
        achievement_score = self._analyze_achievements()
        
        # 6. Action Verbs Analysis
        verb_score = self._analyze_action_verbs()
        
        # 7. Formatting Quality Analysis
        formatting_score = self._analyze_formatting()
        
        # 8. Content Depth Analysis
        content_score = self._analyze_content_depth()
        
        # 9. ATS Compatibility Check
        ats_compat_score = self._check_ats_compatibility()
        
        # 10. Job Description Match (if provided)
        jd_match_score = self._analyze_jd_match() if self.job_description else 70
        
        # Calculate weighted final score
        final_score = self._calculate_final_score({
            'contact': (contact_score, 0.08),
            'structure': (structure_score, 0.12),
            'keywords': (keyword_analysis['keyword_score'], 0.20),
            'achievements': (achievement_score, 0.18),
            'verbs': (verb_score, 0.08),
            'formatting': (formatting_score, 0.12),
            'content': (content_score, 0.12),
            'ats_compat': (ats_compat_score, 0.05),
            'jd_match': (jd_match_score, 0.05)
        })
        
        # Generate insights
        strengths = self._generate_strengths()
        improvements = self._generate_improvements()
        recommendations = self._generate_recommendations()
        
        return {
            'ats_score': final_score,
            'keyword_analysis': keyword_analysis,
            'formatting_score': formatting_score,
            'content_quality_score': content_score,
            'impact_score': achievement_score,
            'strengths': strengths,
            'areas_for_improvement': improvements,
            'recommendations': recommendations,
            'detailed_metrics': self.metrics
        }
    
    def _analyze_document_metrics(self):
        """Calculate basic document metrics"""
        words = self.resume_text.split()
        sentences = [s for s in re.split(r'[.!?]', self.resume_text) if s.strip()]
        paragraphs = [p for p in self.resume_text.split('\n\n') if p.strip()]
        lines = [l for l in self.resume_text.split('\n') if l.strip()]
        
        self.metrics['word_count'] = len(words)
        self.metrics['sentence_count'] = len(sentences)
        self.metrics['paragraph_count'] = len(paragraphs)
        self.metrics['line_count'] = len(lines)
        self.metrics['avg_sentence_length'] = len(words) / max(len(sentences), 1)
        self.metrics['char_count'] = len(self.resume_text)
        
    def _analyze_contact_info(self) -> int:
        """Analyze contact information completeness"""
        score = 0
        max_score = 100
        
        # Email check (25 points)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if re.search(email_pattern, self.resume_text):
            score += 25
            self.metrics['has_email'] = True
        else:
            self.metrics['has_email'] = False
        
        # Phone check (25 points)
        phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
        if re.search(phone_pattern, self.resume_text):
            score += 25
            self.metrics['has_phone'] = True
        else:
            self.metrics['has_phone'] = False
        
        # LinkedIn check (20 points)
        if 'linkedin' in self.resume_lower:
            score += 20
            self.metrics['has_linkedin'] = True
        else:
            self.metrics['has_linkedin'] = False
        
        # Location check (15 points)
        location_indicators = ['city', 'state', 'country', 'location', 'address', 'remote']
        if any(loc in self.resume_lower for loc in location_indicators) or re.search(r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b', self.resume_text):
            score += 15
            self.metrics['has_location'] = True
        else:
            self.metrics['has_location'] = False
        
        # Professional link (GitHub, Portfolio) (15 points)
        if any(site in self.resume_lower for site in ['github', 'portfolio', 'gitlab', 'bitbucket', 'website']):
            score += 15
            self.metrics['has_professional_link'] = True
        else:
            self.metrics['has_professional_link'] = False
        
        self.scores['contact'] = score
        return score
    
    def _analyze_structure(self) -> int:
        """Analyze resume structure and sections"""
        score = 0
        found_sections = []
        
        # Check for essential sections
        section_patterns = {
            'contact': r'(contact|email|phone)',
            'experience': r'(experience|work\s*history|employment|professional\s*experience)',
            'education': r'(education|academic|degree|university|college)',
            'skills': r'(skills|technical\s*skills|competencies|expertise|proficiencies)',
            'summary': r'(summary|objective|profile|about\s*me|professional\s*summary)',
            'projects': r'(projects|portfolio|work\s*samples)',
            'certifications': r'(certifications?|licenses?|credentials)',
            'achievements': r'(achievements?|accomplishments?|awards?|honors?)'
        }
        
        for section, pattern in section_patterns.items():
            if re.search(pattern, self.resume_lower):
                found_sections.append(section)
        
        self.metrics['found_sections'] = found_sections
        
        # Score based on sections (essential: 15 each, recommended: 10 each)
        for section in self.ESSENTIAL_SECTIONS:
            if section in found_sections:
                score += 17
        
        for section in self.RECOMMENDED_SECTIONS:
            if section in found_sections:
                score += 8
        
        # Check for clear section headers (10 points)
        header_patterns = re.findall(r'^\s*[A-Z][A-Z\s]{2,25}:?\s*$', self.resume_text, re.MULTILINE)
        if len(header_patterns) >= 3:
            score += 10
            self.metrics['clear_headers'] = True
        else:
            self.metrics['clear_headers'] = len(header_patterns) >= 1
        
        # Check chronological order (detect dates and order)
        years = re.findall(r'\b(19|20)\d{2}\b', self.resume_text)
        if years:
            self.metrics['has_dates'] = True
            # Check if roughly descending (most recent first)
            if len(years) >= 2:
                year_ints = [int(y) for y in years[:6]]  # Check first 6 years found
                is_chronological = all(year_ints[i] >= year_ints[i+1] for i in range(len(year_ints)-1))
                if is_chronological or sum(1 for i in range(len(year_ints)-1) if year_ints[i] >= year_ints[i+1]) > len(year_ints) // 2:
                    score += 5
        
        self.scores['structure'] = min(score, 100)
        return min(score, 100)
    
    def _analyze_keywords(self) -> Dict:
        """Comprehensive keyword analysis"""
        found_keywords = []
        missing_keywords = []
        
        # Analyze technical keywords
        for category, keywords in self.TECH_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in self.resume_lower:
                    found_keywords.append(keyword)
        
        # Analyze business keywords
        for category, keywords in self.BUSINESS_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in self.resume_lower:
                    found_keywords.append(keyword)
        
        # If job description provided, extract and match keywords
        jd_keywords = []
        if self.job_description:
            # Extract potential keywords from JD
            jd_words = re.findall(r'\b[A-Za-z][A-Za-z\+\#\.]+\b', self.job_description)
            jd_keywords = [w for w in jd_words if len(w) > 2 and w.lower() not in 
                         ['the', 'and', 'for', 'are', 'with', 'will', 'you', 'our', 'your', 'this', 'that', 'have', 'has', 'from', 'they', 'been', 'were', 'being', 'what', 'when', 'where', 'which', 'who', 'also', 'can', 'may', 'must', 'should', 'would', 'could', 'than', 'then', 'only', 'just', 'into', 'over', 'such', 'very', 'some', 'other']]
            
            # Count frequency in JD to find important keywords
            jd_keyword_freq = {}
            for kw in jd_keywords:
                kw_lower = kw.lower()
                jd_keyword_freq[kw_lower] = jd_keyword_freq.get(kw_lower, 0) + 1
            
            # Get top JD keywords
            top_jd_keywords = sorted(jd_keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            
            for kw, freq in top_jd_keywords:
                if kw in self.resume_lower:
                    if kw not in [k.lower() for k in found_keywords]:
                        found_keywords.append(kw)
                else:
                    missing_keywords.append(kw)
        
        # If no JD, suggest common missing keywords based on industry detection
        if not self.job_description:
            # Detect likely industry from resume
            tech_count = sum(1 for k in found_keywords if k.lower() in str(self.TECH_KEYWORDS).lower())
            
            if tech_count > 5:
                # Suggest tech keywords
                for category, keywords in self.TECH_KEYWORDS.items():
                    for kw in keywords[:3]:
                        if kw.lower() not in self.resume_lower and kw not in missing_keywords:
                            missing_keywords.append(kw)
                            if len(missing_keywords) >= 8:
                                break
                    if len(missing_keywords) >= 8:
                        break
            else:
                # Suggest business keywords
                for category, keywords in self.BUSINESS_KEYWORDS.items():
                    for kw in keywords[:3]:
                        if kw.lower() not in self.resume_lower and kw not in missing_keywords:
                            missing_keywords.append(kw)
                            if len(missing_keywords) >= 8:
                                break
                    if len(missing_keywords) >= 8:
                        break
        
        # Calculate keyword score
        keyword_count = len(found_keywords)
        
        if keyword_count >= 25:
            keyword_score = 95
        elif keyword_count >= 20:
            keyword_score = 88
        elif keyword_count >= 15:
            keyword_score = 80
        elif keyword_count >= 10:
            keyword_score = 70
        elif keyword_count >= 7:
            keyword_score = 60
        elif keyword_count >= 5:
            keyword_score = 50
        elif keyword_count >= 3:
            keyword_score = 40
        else:
            keyword_score = max(20, keyword_count * 10)
        
        # Boost if job description match is high
        if self.job_description and missing_keywords:
            match_ratio = len(found_keywords) / max(len(found_keywords) + len(missing_keywords[:10]), 1)
            if match_ratio > 0.7:
                keyword_score = min(keyword_score + 10, 100)
        
        self.metrics['keyword_count'] = keyword_count
        self.metrics['found_keywords'] = found_keywords[:20]
        self.metrics['missing_keywords'] = missing_keywords[:10]
        self.scores['keywords'] = keyword_score
        
        return {
            'keyword_score': keyword_score,
            'present_keywords': found_keywords[:15],
            'missing_keywords': missing_keywords[:8]
        }
    
    def _analyze_achievements(self) -> int:
        """Analyze quantified achievements and impact statements"""
        score = 0
        
        # Find quantified achievements (numbers with context)
        quantified_patterns = [
            r'\d+%',  # Percentages
            r'\$[\d,]+[KkMmBb]?',  # Dollar amounts
            r'[\d,]+\+?\s*(users?|customers?|clients?|members?|employees?)',  # User counts
            r'(increased?|decreased?|reduced?|improved?|grew?|saved?|generated?)\s*.*?\d+',  # Impact with numbers
            r'\d+x\s*(faster|better|more|improvement)',  # Multipliers
            r'(top|first|#1|\d+(?:st|nd|rd|th))',  # Rankings
            r'\d+\s*(projects?|teams?|products?|applications?)',  # Counts
        ]
        
        quantified_count = 0
        for pattern in quantified_patterns:
            matches = re.findall(pattern, self.resume_lower)
            quantified_count += len(matches)
        
        self.metrics['quantified_achievements'] = quantified_count
        
        # Score based on quantified achievements
        if quantified_count >= 10:
            score = 95
        elif quantified_count >= 7:
            score = 85
        elif quantified_count >= 5:
            score = 75
        elif quantified_count >= 3:
            score = 65
        elif quantified_count >= 2:
            score = 55
        elif quantified_count >= 1:
            score = 45
        else:
            score = 25
        
        self.scores['achievements'] = score
        return score
    
    def _analyze_action_verbs(self) -> int:
        """Analyze action verb usage and variety"""
        high_impact = []
        medium_impact = []
        standard = []
        
        for verb in self.ACTION_VERBS['high_impact']:
            if re.search(rf'\b{verb}\w*\b', self.resume_lower):
                high_impact.append(verb)
        
        for verb in self.ACTION_VERBS['medium_impact']:
            if re.search(rf'\b{verb}\w*\b', self.resume_lower):
                medium_impact.append(verb)
        
        for verb in self.ACTION_VERBS['standard']:
            if re.search(rf'\b{verb}\w*\b', self.resume_lower):
                standard.append(verb)
        
        self.metrics['high_impact_verbs'] = high_impact
        self.metrics['medium_impact_verbs'] = medium_impact
        self.metrics['standard_verbs'] = standard
        
        total_verbs = len(high_impact) + len(medium_impact) + len(standard)
        
        # Calculate score with emphasis on high-impact verbs
        score = min(100, (len(high_impact) * 8) + (len(medium_impact) * 4) + (len(standard) * 2))
        
        # Bonus for verb variety
        if total_verbs >= 10 and len(high_impact) >= 3:
            score = min(100, score + 15)
        
        self.scores['verbs'] = score
        return score
    
    def _analyze_formatting(self) -> int:
        """Analyze document formatting for ATS compatibility"""
        score = 70  # Start with baseline
        
        # Check for bullet points (good for ATS)
        bullet_count = self.resume_text.count('•') + self.resume_text.count('●') + self.resume_text.count('■')
        line_dash_bullets = len(re.findall(r'^\s*[-*]\s+', self.resume_text, re.MULTILINE))
        total_bullets = bullet_count + line_dash_bullets
        
        self.metrics['bullet_points'] = total_bullets
        
        if total_bullets >= 15:
            score += 15
        elif total_bullets >= 10:
            score += 10
        elif total_bullets >= 5:
            score += 5
        
        # Check word count (optimal: 400-800)
        word_count = self.metrics.get('word_count', 0)
        if 400 <= word_count <= 800:
            score += 10
            self.metrics['optimal_length'] = True
        elif 300 <= word_count <= 1000:
            score += 5
            self.metrics['optimal_length'] = False
        else:
            self.metrics['optimal_length'] = False
            score -= 5
        
        # Penalize potential ATS-unfriendly elements
        # Tables, graphics, columns often break ATS
        if '|' in self.resume_text and self.resume_text.count('|') > 10:
            score -= 10  # Possible table
            self.metrics['possible_table'] = True
        else:
            self.metrics['possible_table'] = False
        
        # Check for consistent date formatting
        date_formats = re.findall(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}\b|\b\d{1,2}/\d{4}\b|\b\d{4}\s*-\s*(?:\d{4}|present|current)\b', self.resume_text, re.IGNORECASE)
        if len(date_formats) >= 4:
            score += 5
            self.metrics['consistent_dates'] = True
        else:
            self.metrics['consistent_dates'] = len(date_formats) >= 2
        
        self.scores['formatting'] = max(0, min(100, score))
        return max(0, min(100, score))
    
    def _analyze_content_depth(self) -> int:
        """Analyze content depth and quality"""
        score = 50  # Baseline
        
        word_count = self.metrics.get('word_count', 0)
        sentence_count = self.metrics.get('sentence_count', 0)
        
        # Evaluate experience detail
        experience_section = re.search(r'(?:experience|work\s*history|employment).*?(?=\n\s*[A-Z]{2,}|\Z)', self.resume_text, re.IGNORECASE | re.DOTALL)
        if experience_section:
            exp_text = experience_section.group()
            exp_word_count = len(exp_text.split())
            if exp_word_count >= 200:
                score += 20
            elif exp_word_count >= 100:
                score += 10
        
        # Check for career progression indicators
        progression_terms = ['senior', 'lead', 'manager', 'director', 'principal', 'architect', 'head', 'chief', 'vp', 'promoted', 'advanced']
        progression_found = sum(1 for term in progression_terms if term in self.resume_lower)
        if progression_found >= 2:
            score += 15
        elif progression_found >= 1:
            score += 8
        
        self.metrics['career_progression'] = progression_found
        
        # Check for industry-specific depth
        technical_depth = len(self.metrics.get('found_keywords', []))
        if technical_depth >= 15:
            score += 15
        elif technical_depth >= 10:
            score += 10
        elif technical_depth >= 5:
            score += 5
        
        self.scores['content'] = max(0, min(100, score))
        return max(0, min(100, score))
    
    def _check_ats_compatibility(self) -> int:
        """Check for ATS-friendly elements"""
        score = 80  # Start optimistic
        
        # Check for problematic characters
        problematic_chars = ['→', '←', '↑', '↓', '★', '☆', '✓', '✗', '©', '®', '™']
        problem_count = sum(self.resume_text.count(char) for char in problematic_chars)
        if problem_count > 5:
            score -= 15
        elif problem_count > 0:
            score -= 5
        
        self.metrics['problematic_chars'] = problem_count
        
        # Check for standard font indicators (no actual fonts, just unusual patterns)
        if re.search(r'[^\x00-\x7F]{10,}', self.resume_text):  # Long non-ASCII strings
            score -= 10
        
        # Positive: clean section headers
        if self.metrics.get('clear_headers', False):
            score += 10
        
        # Positive: bullet points
        if self.metrics.get('bullet_points', 0) >= 5:
            score += 10
        
        self.scores['ats_compat'] = max(0, min(100, score))
        return max(0, min(100, score))
    
    def _analyze_jd_match(self) -> int:
        """Analyze match with job description"""
        if not self.job_description:
            return 70
        
        # Extract important words from JD
        jd_words = set(re.findall(r'\b[A-Za-z]{4,}\b', self.job_desc_lower))
        resume_words = set(re.findall(r'\b[A-Za-z]{4,}\b', self.resume_lower))
        
        # Remove common words
        common = {'with', 'that', 'this', 'have', 'from', 'they', 'will', 'your', 'about', 'been', 'more', 'when', 'there', 'which', 'their', 'would', 'could', 'should', 'other'}
        jd_words -= common
        resume_words -= common
        
        if not jd_words:
            return 70
        
        # Calculate match percentage
        matches = jd_words.intersection(resume_words)
        match_percentage = len(matches) / len(jd_words) * 100
        
        self.metrics['jd_match_percentage'] = round(match_percentage, 1)
        self.scores['jd_match'] = min(100, int(match_percentage * 1.2))  # Slight boost
        
        return min(100, int(match_percentage * 1.2))
    
    def _calculate_final_score(self, weighted_scores: Dict) -> int:
        """Calculate final weighted score"""
        total = 0
        total_weight = 0
        
        for category, (score, weight) in weighted_scores.items():
            total += score * weight
            total_weight += weight
        
        final = int(total / total_weight) if total_weight > 0 else 50
        
        # Apply realistic ceiling based on missing critical elements
        if not self.metrics.get('has_email', False):
            final = min(final, 80)
        if self.metrics.get('quantified_achievements', 0) == 0:
            final = min(final, 70)
        if len(self.metrics.get('found_sections', [])) < 3:
            final = min(final, 65)
        
        return max(0, min(100, final))
    
    def _generate_strengths(self) -> List[str]:
        """Generate list of strengths based on analysis"""
        strengths = []
        
        if self.metrics.get('quantified_achievements', 0) >= 5:
            strengths.append(f"Strong use of quantified achievements ({self.metrics['quantified_achievements']} measurable results identified)")
        elif self.metrics.get('quantified_achievements', 0) >= 2:
            strengths.append("Includes quantified achievements demonstrating measurable impact")
        
        if len(self.metrics.get('high_impact_verbs', [])) >= 3:
            strengths.append("Excellent use of high-impact action verbs that convey leadership and results")
        
        if self.metrics.get('keyword_count', 0) >= 15:
            strengths.append(f"Rich keyword content with {self.metrics['keyword_count']}+ relevant professional terms")
        elif self.metrics.get('keyword_count', 0) >= 10:
            strengths.append("Good industry-relevant keyword coverage")
        
        if self.scores.get('formatting', 0) >= 80:
            strengths.append("Clean, ATS-optimized formatting with effective use of bullet points")
        
        if self.metrics.get('has_linkedin', False) and self.metrics.get('has_professional_link', False):
            strengths.append("Professional online presence with LinkedIn and portfolio links")
        elif self.metrics.get('has_linkedin', False):
            strengths.append("Includes LinkedIn profile for professional networking")
        
        if len(self.metrics.get('found_sections', [])) >= 5:
            strengths.append("Comprehensive resume structure with all essential and recommended sections")
        elif len(self.metrics.get('found_sections', [])) >= 4:
            strengths.append("Well-organized resume with clear section structure")
        
        if self.metrics.get('career_progression', 0) >= 2:
            strengths.append("Demonstrates clear career progression and professional growth")
        
        if 400 <= self.metrics.get('word_count', 0) <= 700:
            strengths.append("Optimal resume length for ATS parsing and recruiter review")
        
        # Ensure we have at least 4 strengths
        default_strengths = [
            "Resume successfully parsed without critical ATS errors",
            "Contact information properly formatted for ATS extraction",
            "Professional language and tone throughout document"
        ]
        
        while len(strengths) < 4:
            for s in default_strengths:
                if s not in strengths and len(strengths) < 4:
                    strengths.append(s)
        
        return strengths[:6]
    
    def _generate_improvements(self) -> List[str]:
        """Generate list of improvement areas"""
        improvements = []
        
        if self.metrics.get('quantified_achievements', 0) < 3:
            improvements.append("Add more quantified achievements with specific metrics (percentages, dollar amounts, user counts)")
        
        if self.metrics.get('keyword_count', 0) < 10:
            improvements.append("Incorporate more industry-relevant keywords and technical terminology")
        
        if not self.metrics.get('has_linkedin', False):
            improvements.append("Add LinkedIn profile URL to strengthen professional presence")
        
        if len(self.metrics.get('high_impact_verbs', [])) < 3:
            improvements.append("Replace passive language with high-impact action verbs (achieved, delivered, transformed)")
        
        if not self.metrics.get('optimal_length', False):
            word_count = self.metrics.get('word_count', 0)
            if word_count < 400:
                improvements.append("Expand content with more detail about achievements and responsibilities (aim for 400-700 words)")
            elif word_count > 800:
                improvements.append("Consider condensing content to 1-2 pages for optimal recruiter attention")
        
        if self.metrics.get('bullet_points', 0) < 10:
            improvements.append("Use more bullet points to improve readability and ATS parsing")
        
        missing_sections = [s for s in self.ESSENTIAL_SECTIONS + self.RECOMMENDED_SECTIONS[:2] 
                          if s not in self.metrics.get('found_sections', [])]
        if missing_sections:
            improvements.append(f"Consider adding missing sections: {', '.join(missing_sections[:3])}")
        
        if self.scores.get('jd_match', 100) < 60 and self.job_description:
            improvements.append("Tailor resume content to better match the specific job requirements")
        
        return improvements[:6]
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = [
            f"Quantify your impact: Transform statements like 'improved sales' into 'increased sales by 25% ($2M revenue)' - you currently have {self.metrics.get('quantified_achievements', 0)} quantified achievements",
            "Use the STAR method (Situation, Task, Action, Result) for each experience bullet point",
            "Mirror key terms from job descriptions - ATS systems scan for exact keyword matches",
            "Place most relevant skills and keywords in the top third of your resume for visibility",
            "Update your LinkedIn profile to match your resume for consistency across platforms"
        ]
        
        if self.metrics.get('keyword_count', 0) < 15:
            recommendations.insert(0, f"Increase keyword density: Add {15 - self.metrics.get('keyword_count', 0)} more relevant technical/industry terms throughout your resume")
        
        if not self.metrics.get('has_professional_link', False):
            recommendations.append("Add a GitHub or portfolio link to showcase your work samples")
        
        if self.scores.get('achievements', 0) < 60:
            recommendations.insert(1, "Focus on outcomes over duties: Replace 'Responsible for...' with 'Achieved/Delivered...'")
        
        return recommendations[:7]


# ============================================
# AI-ENHANCED ANALYSIS FUNCTION
# ============================================

async def analyze_resume_with_hybrid_approach(resume_text: str, job_description: str = "") -> dict:
    """
    Hybrid analysis combining deterministic scoring with AI insights
    """
    
    # First, run deterministic analysis (always reliable)
    analyzer = DeterministicATSAnalyzer(resume_text, job_description)
    deterministic_results = analyzer.analyze()
    
    # Try to enhance with AI analysis
    api_key = os.getenv("GROQ_API_KEY")
    ai_insights = None
    
    if api_key:
        ai_insights = await get_ai_analysis(resume_text, job_description, api_key)
    
    # Merge results, prioritizing deterministic scoring but incorporating AI insights
    final_results = merge_analysis_results(deterministic_results, ai_insights)
    
    return final_results


async def get_ai_analysis(resume_text: str, job_description: str, api_key: str) -> Optional[Dict]:
    """Get AI-powered analysis for deeper insights"""
    
    prompt = f"""You are an expert ATS (Applicant Tracking System) analyst and career coach. Analyze this resume and provide specific, actionable insights.

RESUME:
{resume_text[:4000]}

{"JOB DESCRIPTION:" + chr(10) + job_description[:1500] if job_description else "No specific job description provided - analyze for general ATS optimization."}

Provide your analysis in this exact JSON format:
{{
    "ai_score_adjustment": <integer from -10 to +10, adjustment to base score>,
    "ai_overall_feedback": "<2-3 sentence professional assessment>",
    "ai_strengths": ["<specific strength 1>", "<specific strength 2>"],
    "ai_improvements": ["<specific improvement 1>", "<specific improvement 2>"],
    "ai_keyword_suggestions": ["<keyword 1>", "<keyword 2>", "<keyword 3>"],
    "ai_recommendations": ["<actionable recommendation 1>", "<actionable recommendation 2>"]
}}

Be specific and reference actual content from the resume. Focus on:
1. Content quality and professional impact
2. Industry-specific insights
3. Unique strengths or concerns the deterministic analysis might miss
4. Career positioning advice

Return ONLY valid JSON, no other text."""

    content = None
    
    # Try SDK first
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
                    max_tokens=1500
                )
                content = response.choices[0].message.content
        except Exception as e:
            print(f"Groq SDK failed: {e}")
    
    # Fallback to direct API
    if content is None:
        content = groq_direct_api(prompt, api_key)
    
    if content:
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing AI response: {e}")
    
    return None


def merge_analysis_results(deterministic: Dict, ai_insights: Optional[Dict]) -> Dict:
    """Merge deterministic and AI analysis results"""
    
    # Start with deterministic results as base
    result = deterministic.copy()
    
    if ai_insights:
        # Adjust score based on AI analysis (limited adjustment)
        score_adjustment = ai_insights.get('ai_score_adjustment', 0)
        score_adjustment = max(-10, min(10, score_adjustment))  # Clamp to ±10
        result['ats_score'] = max(0, min(100, result['ats_score'] + score_adjustment))
        
        # Enhance feedback with AI insights
        if ai_insights.get('ai_overall_feedback'):
            result['overall_feedback'] = ai_insights['ai_overall_feedback']
        else:
            result['overall_feedback'] = generate_feedback(result['ats_score'])
        
        # Merge strengths (AI first, then deterministic)
        ai_strengths = ai_insights.get('ai_strengths', [])
        combined_strengths = ai_strengths[:2] + [s for s in result['strengths'] if s not in ai_strengths]
        result['strengths'] = combined_strengths[:6]
        
        # Merge improvements
        ai_improvements = ai_insights.get('ai_improvements', [])
        combined_improvements = ai_improvements[:2] + [i for i in result['areas_for_improvement'] if i not in ai_improvements]
        result['areas_for_improvement'] = combined_improvements[:6]
        
        # Merge keyword suggestions
        ai_keywords = ai_insights.get('ai_keyword_suggestions', [])
        if ai_keywords:
            existing_missing = result['keyword_analysis'].get('missing_keywords', [])
            combined_missing = ai_keywords[:3] + [k for k in existing_missing if k not in ai_keywords]
            result['keyword_analysis']['missing_keywords'] = combined_missing[:8]
        
        # Merge recommendations
        ai_recs = ai_insights.get('ai_recommendations', [])
        combined_recs = ai_recs[:2] + [r for r in result['recommendations'] if r not in ai_recs]
        result['recommendations'] = combined_recs[:7]
    
    else:
        # Generate feedback without AI
        result['overall_feedback'] = generate_feedback(result['ats_score'])
    
    return result


def generate_feedback(score: int) -> str:
    """Generate feedback based on score"""
    if score >= 90:
        return f"Exceptional resume with a score of {score}/100! Your resume demonstrates outstanding ATS optimization with strong quantified achievements, excellent keyword coverage, and professional formatting. You're well-positioned for top-tier opportunities."
    elif score >= 80:
        return f"Excellent resume scoring {score}/100. Your resume shows strong ATS compatibility with good keyword usage and clear structure. Minor optimizations could push you into the exceptional range."
    elif score >= 70:
        return f"Very good resume with a score of {score}/100. You have a solid foundation with room for improvement. Focus on adding more quantified achievements and industry-specific keywords."
    elif score >= 60:
        return f"Good resume scoring {score}/100. Your resume has potential but needs optimization. Prioritize adding measurable results and tailoring content to specific job descriptions."
    elif score >= 50:
        return f"Fair resume with a score of {score}/100. There's significant room for improvement. Focus on quantifying achievements, adding relevant keywords, and improving document structure."
    elif score >= 40:
        return f"Your resume scores {score}/100 and needs substantial work. Review the recommendations below and prioritize adding quantified achievements and industry keywords."
    else:
        return f"Your resume scores {score}/100 and requires significant revision. Focus on adding essential sections, quantified achievements, and proper formatting for ATS compatibility."


# ============================================
# API ENDPOINTS
# ============================================

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
    
    # Run hybrid analysis (deterministic + AI)
    analysis = await analyze_resume_with_hybrid_approach(resume_text, job_description or "")
    
    return JSONResponse(content=analysis)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0"}

# For Vercel deployment
app.mount("/", app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
