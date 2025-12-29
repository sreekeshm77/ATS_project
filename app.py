from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import json
import os
import io
import fitz  # PyMuPDF for PDF
import docx2txt
from typing import Optional, List
import re
from datetime import datetime

# Load API key
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Create the FastAPI app instance
app = FastAPI(title="AI ATS Resume Checker API", version="1.0.0")

# For Vercel deployment compatibility
application = app

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT_BASE = """
You are an expert ATS (Applicant Tracking System) Resume Evaluator with 10+ years of experience in recruitment and HR technology.

Analyze the resume comprehensively and provide detailed feedback. Consider:

1. ATS Compatibility (formatting, keywords, structure)
2. Content Quality (experience, skills, achievements)
3. Professional Presentation (clarity, conciseness, impact)
4. Keyword Optimization (industry-specific terms)
5. Overall Marketability

If a job description is provided, also evaluate:
- Job requirement alignment
- Keyword matching
- Skills gap analysis
- Suitability for the specific role

Return ONLY valid JSON in this exact format:

{
  "ats_score": 85,
  "summary_feedback": "Overall assessment with key strengths and areas for improvement",
  "skills_feedback": "Analysis of technical and soft skills presentation",
  "experience_feedback": "Evaluation of work experience and achievements",
  "education_feedback": "Assessment of educational background and certifications",
  "formatting_feedback": "ATS-friendly formatting and structure analysis",
  "pros": ["Clear professional summary", "Strong technical skills", "Quantified achievements"],
  "cons": ["Missing keywords", "Inconsistent formatting", "Lacks specific metrics"],
  "recommendations": ["Add more industry keywords", "Include quantified results", "Optimize section headers"],
  "matched_keywords": ["Python", "Machine Learning", "Project Management"],
  "missing_keywords": ["SQL", "Cloud Computing", "Agile"],
  "improvement_areas": ["Technical Skills", "Professional Summary", "Work Experience"],
  "strengths": ["Strong Educational Background", "Relevant Experience", "Clear Structure"]
}
"""

class AnalysisResult(BaseModel):
    ats_score: int
    summary_feedback: str
    skills_feedback: str
    experience_feedback: str
    education_feedback: str
    formatting_feedback: str
    pros: List[str]
    cons: List[str]
    recommendations: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    improvement_areas: List[str]
    strengths: List[str]

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file bytes"""
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file bytes"""
    try:
        return docx2txt.process(io.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")

def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from TXT file bytes"""
    try:
        return file_bytes.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading TXT: {str(e)}")

def call_groq_ai(resume_text: str, job_description: str = "") -> dict:
    """Call the Groq API to analyze resume"""
    user_prompt = f"""
RESUME CONTENT:
{resume_text}

JOB DESCRIPTION:
{job_description if job_description else 'No specific job description provided - provide general ATS optimization feedback'}

Please analyze this resume thoroughly and provide detailed feedback following the JSON format specified.
"""
    
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_BASE},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=30)
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            
            # Clean the content to ensure it's valid JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                result = json.loads(content)
                
                # Validate required fields and set defaults if missing
                required_fields = {
                    "ats_score": 0,
                    "summary_feedback": "Unable to generate feedback",
                    "skills_feedback": "Unable to analyze skills",
                    "experience_feedback": "Unable to analyze experience", 
                    "education_feedback": "Unable to analyze education",
                    "formatting_feedback": "Unable to analyze formatting",
                    "pros": [],
                    "cons": [],
                    "recommendations": [],
                    "matched_keywords": [],
                    "missing_keywords": [],
                    "improvement_areas": [],
                    "strengths": []
                }
                
                for field, default in required_fields.items():
                    if field not in result:
                        result[field] = default
                
                # Ensure score is within valid range
                result["ats_score"] = max(0, min(100, int(result.get("ats_score", 0))))
                
                return result
                
            except json.JSONDecodeError:
                # Fallback response if JSON parsing fails
                return {
                    "ats_score": 50,
                    "summary_feedback": "Unable to parse AI response. Please try again.",
                    "skills_feedback": "Error in analysis",
                    "experience_feedback": "Error in analysis",
                    "education_feedback": "Error in analysis", 
                    "formatting_feedback": "Error in analysis",
                    "pros": ["Resume uploaded successfully"],
                    "cons": ["Unable to complete full analysis"],
                    "recommendations": ["Please try uploading again"],
                    "matched_keywords": [],
                    "missing_keywords": [],
                    "improvement_areas": ["Technical Analysis"],
                    "strengths": ["File Format Compatible"]
                }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"AI service error: {response.text}"
            )
            
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis error: {str(e)}"
        )

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI ATS Resume Checker - Professional Resume Analysis</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }

        .main-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 30px;
        }

        .card-header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .card-body {
            padding: 40px;
        }

        .upload-section {
            margin-bottom: 30px;
        }

        .file-drop-area {
            border: 3px dashed #4facfe;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #f8f9ff;
            position: relative;
            overflow: hidden;
        }

        .file-drop-area:hover {
            border-color: #667eea;
            background: #f0f2ff;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }

        .file-drop-area.dragover {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea20, #764ba220);
            transform: scale(1.02);
        }

        .file-drop-area .upload-icon {
            font-size: 4rem;
            color: #4facfe;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }

        .file-drop-area:hover .upload-icon {
            transform: scale(1.1);
            color: #667eea;
        }

        .file-drop-area .upload-text {
            font-size: 1.3rem;
            color: #333;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .file-drop-area .upload-subtext {
            color: #666;
            font-size: 1rem;
        }

        .selected-file {
            display: none;
            background: linear-gradient(135deg, #00c851, #007e33);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }

        .selected-file.show {
            display: block;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 1.1rem;
        }

        .form-control {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
            resize: vertical;
        }

        .form-control:focus {
            outline: none;
            border-color: #4facfe;
            box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
        }

        .analyze-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 18px 40px;
            border: none;
            border-radius: 50px;
            font-size: 1.2rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: block;
            margin: 30px auto 0;
            min-width: 200px;
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .analyze-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        }

        .analyze-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .loading-spinner {
            display: none;
            text-align: center;
            padding: 40px;
        }

        .loading-spinner.show {
            display: block;
        }

        .spinner {
            width: 60px;
            height: 60px;
            border: 6px solid #f3f3f3;
            border-top: 6px solid #4facfe;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .results-section {
            display: none;
            margin-top: 30px;
        }

        .results-section.show {
            display: block;
            animation: fadeInUp 0.6s ease;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .score-circle {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: conic-gradient(from 0deg, #4facfe, #00f2fe, #4facfe);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 30px;
            position: relative;
        }

        .score-circle::before {
            content: '';
            position: absolute;
            width: 120px;
            height: 120px;
            background: white;
            border-radius: 50%;
        }

        .score-text {
            position: relative;
            z-index: 1;
            font-size: 2.5rem;
            font-weight: bold;
            color: #333;
        }

        .feedback-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .feedback-card {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            border-left: 5px solid #4facfe;
            transition: all 0.3s ease;
        }

        .feedback-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }

        .feedback-card h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        .feedback-card p {
            color: #666;
            line-height: 1.6;
        }

        .pros-cons-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .pros-card {
            background: linear-gradient(135deg, #00c85120, #007e3320);
            border-radius: 15px;
            padding: 25px;
            border-left: 5px solid #00c851;
        }

        .cons-card {
            background: linear-gradient(135deg, #ff444420, #cc000020);
            border-radius: 15px;
            padding: 25px;
            border-left: 5px solid #ff4444;
        }

        .pros-card h3, .cons-card h3 {
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        .pros-card h3 {
            color: #007e33;
        }

        .cons-card h3 {
            color: #cc0000;
        }

        .list-item {
            background: white;
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 8px;
            border-left: 3px solid currentColor;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .keywords-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .keyword-tag {
            display: inline-block;
            background: #4facfe;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            margin: 5px;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .missing-keyword-tag {
            background: #ff4444;
        }

        .recommendations-card {
            background: linear-gradient(135deg, #ffc10720, #fb890320);
            border-radius: 15px;
            padding: 25px;
            border-left: 5px solid #ffc107;
        }

        .recommendations-card h3 {
            color: #b8860b;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .pros-cons-grid, .keywords-section {
                grid-template-columns: 1fr;
            }
            
            .card-body {
                padding: 20px;
            }
        }

        .error-message {
            background: #ff4444;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            display: none;
        }

        .error-message.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-file-alt"></i> AI ATS Resume Checker</h1>
            <p>Get professional feedback and improve your resume's ATS compatibility</p>
        </div>

        <div class="main-card">
            <div class="card-header">
                <h2><i class="fas fa-upload"></i> Upload Your Resume</h2>
                <p>Supported formats: PDF, DOCX, TXT • Get instant AI-powered feedback</p>
            </div>
            
            <div class="card-body">
                <form id="resumeForm">
                    <div class="upload-section">
                        <div class="file-drop-area" id="fileDropArea">
                            <input type="file" id="resumeFile" accept=".pdf,.docx,.txt" style="display: none;">
                            <div id="uploadPrompt">
                                <i class="fas fa-cloud-upload-alt upload-icon"></i>
                                <div class="upload-text">Drop your resume here</div>
                                <div class="upload-subtext">or click to browse files</div>
                            </div>
                        </div>
                        
                        <div class="selected-file" id="selectedFile">
                            <i class="fas fa-check-circle"></i>
                            <span id="fileName"></span>
                            <button type="button" onclick="clearFile()" style="background: none; border: none; color: white; margin-left: 15px; cursor: pointer;">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="jobDescription">
                            <i class="fas fa-briefcase"></i> Job Description (Optional)
                        </label>
                        <textarea 
                            id="jobDescription" 
                            class="form-control"
                            rows="6" 
                            placeholder="Paste the job description here for targeted analysis and better keyword matching..."
                        ></textarea>
                    </div>

                    <button type="submit" class="analyze-btn" id="analyzeBtn">
                        <i class="fas fa-magic"></i> Analyze Resume
                    </button>
                </form>

                <div class="error-message" id="errorMessage"></div>

                <div class="loading-spinner" id="loadingSpinner">
                    <div class="spinner"></div>
                    <h3>Analyzing your resume...</h3>
                    <p>Our AI is carefully reviewing your resume for ATS optimization</p>
                </div>

                <div class="results-section" id="resultsSection">
                    <div class="main-card">
                        <div class="card-header">
                            <h2><i class="fas fa-chart-line"></i> Analysis Results</h2>
                        </div>
                        <div class="card-body" id="resultsContent">
                            <!-- Results will be inserted here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;

        // File upload handling
        const fileDropArea = document.getElementById('fileDropArea');
        const fileInput = document.getElementById('resumeFile');
        const uploadPrompt = document.getElementById('uploadPrompt');
        const selectedFileDiv = document.getElementById('selectedFile');
        const fileName = document.getElementById('fileName');

        fileDropArea.addEventListener('click', () => fileInput.click());
        
        fileDropArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileDropArea.classList.add('dragover');
        });
        
        fileDropArea.addEventListener('dragleave', () => {
            fileDropArea.classList.remove('dragover');
        });
        
        fileDropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileDropArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });

        function handleFileSelect(file) {
            const validTypes = ['.pdf', '.docx', '.txt'];
            const fileType = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!validTypes.includes(fileType)) {
                showError('Please upload a PDF, DOCX, or TXT file.');
                return;
            }
            
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                showError('File size must be less than 10MB.');
                return;
            }
            
            selectedFile = file;
            fileName.textContent = file.name;
            uploadPrompt.style.display = 'none';
            selectedFileDiv.classList.add('show');
            hideError();
        }

        function clearFile() {
            selectedFile = null;
            fileInput.value = '';
            uploadPrompt.style.display = 'block';
            selectedFileDiv.classList.remove('show');
        }

        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.classList.add('show');
        }

        function hideError() {
            document.getElementById('errorMessage').classList.remove('show');
        }

        // Form submission
        document.getElementById('resumeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!selectedFile) {
                showError('Please upload a resume file to continue.');
                return;
            }

            const formData = new FormData();
            formData.append('resume_file', selectedFile);
            formData.append('job_description', document.getElementById('jobDescription').value);

            // Show loading state
            document.getElementById('loadingSpinner').classList.add('show');
            document.getElementById('resultsSection').classList.remove('show');
            document.getElementById('analyzeBtn').disabled = true;
            hideError();

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.detail || 'Analysis failed. Please try again.');
                }

                displayResults(result);
            } catch (error) {
                showError(error.message || 'An error occurred. Please try again.');
                console.error('Analysis error:', error);
            } finally {
                document.getElementById('loadingSpinner').classList.remove('show');
                document.getElementById('analyzeBtn').disabled = false;
            }
        });

        function displayResults(result) {
            const resultsContent = document.getElementById('resultsContent');
            
            // Ensure arrays exist
            const pros = result.pros || [];
            const cons = result.cons || [];
            const recommendations = result.recommendations || [];
            const matchedKeywords = result.matched_keywords || [];
            const missingKeywords = result.missing_keywords || [];
            const strengths = result.strengths || [];
            const improvementAreas = result.improvement_areas || [];
            
            resultsContent.innerHTML = `
                <!-- ATS Score -->
                <div style="text-align: center; margin-bottom: 40px;">
                    <div class="score-circle">
                        <div class="score-text">${result.ats_score}</div>
                    </div>
                    <h2 style="color: #333; margin-bottom: 10px;">ATS Compatibility Score</h2>
                    <p style="color: #666; font-size: 1.1rem;">Your resume scored ${result.ats_score} out of 100</p>
                </div>

                <!-- Detailed Feedback -->
                <div class="feedback-grid">
                    <div class="feedback-card">
                        <h3><i class="fas fa-user"></i> Summary Analysis</h3>
                        <p>${result.summary_feedback || 'No summary feedback available.'}</p>
                    </div>
                    <div class="feedback-card">
                        <h3><i class="fas fa-cogs"></i> Skills Assessment</h3>
                        <p>${result.skills_feedback || 'No skills feedback available.'}</p>
                    </div>
                    <div class="feedback-card">
                        <h3><i class="fas fa-briefcase"></i> Experience Review</h3>
                        <p>${result.experience_feedback || 'No experience feedback available.'}</p>
                    </div>
                    <div class="feedback-card">
                        <h3><i class="fas fa-graduation-cap"></i> Education Analysis</h3>
                        <p>${result.education_feedback || 'No education feedback available.'}</p>
                    </div>
                    <div class="feedback-card">
                        <h3><i class="fas fa-file-alt"></i> Formatting Review</h3>
                        <p>${result.formatting_feedback || 'No formatting feedback available.'}</p>
                    </div>
                    <div class="feedback-card">
                        <h3><i class="fas fa-star"></i> Overall Assessment</h3>
                        <p><strong>Strengths:</strong> ${strengths.join(', ') || 'None specified'}</p>
                        <p style="margin-top: 10px;"><strong>Areas to Improve:</strong> ${improvementAreas.join(', ') || 'None specified'}</p>
                    </div>
                </div>

                <!-- Pros and Cons -->
                <div class="pros-cons-grid">
                    <div class="pros-card">
                        <h3><i class="fas fa-thumbs-up"></i> Strengths</h3>
                        ${pros.length > 0 ? pros.map(pro => `<div class="list-item" style="color: #007e33;">${pro}</div>`).join('') : '<div class="list-item" style="color: #007e33;">Resume uploaded successfully</div>'}
                    </div>
                    <div class="cons-card">
                        <h3><i class="fas fa-thumbs-down"></i> Areas for Improvement</h3>
                        ${cons.length > 0 ? cons.map(con => `<div class="list-item" style="color: #cc0000;">${con}</div>`).join('') : '<div class="list-item" style="color: #cc0000;">No specific issues identified</div>'}
                    </div>
                </div>

                <!-- Keywords Analysis -->
                <div class="keywords-section">
                    <div style="background: linear-gradient(135deg, #4facfe20, #00f2fe20); border-radius: 15px; padding: 25px; border-left: 5px solid #4facfe;">
                        <h3 style="color: #2c5aa0; margin-bottom: 15px;"><i class="fas fa-check-circle"></i> Matched Keywords</h3>
                        <div>
                            ${matchedKeywords.length > 0 ? matchedKeywords.map(keyword => `<span class="keyword-tag">${keyword}</span>`).join('') : '<span class="keyword-tag">No keywords matched</span>'}
                        </div>
                    </div>
                    <div style="background: linear-gradient(135deg, #ff444420, #cc000020); border-radius: 15px; padding: 25px; border-left: 5px solid #ff4444;">
                        <h3 style="color: #cc0000; margin-bottom: 15px;"><i class="fas fa-exclamation-triangle"></i> Missing Keywords</h3>
                        <div>
                            ${missingKeywords.length > 0 ? missingKeywords.map(keyword => `<span class="keyword-tag missing-keyword-tag">${keyword}</span>`).join('') : '<span class="keyword-tag missing-keyword-tag">No missing keywords identified</span>'}
                        </div>
                    </div>
                </div>

                <!-- Recommendations -->
                <div class="recommendations-card">
                    <h3><i class="fas fa-lightbulb"></i> Improvement Recommendations</h3>
                    ${recommendations.length > 0 ? recommendations.map(rec => `<div class="list-item" style="color: #b8860b; margin-bottom: 10px;">${rec}</div>`).join('') : '<div class="list-item" style="color: #b8860b;">No specific recommendations at this time.</div>'}
                </div>
            `;

            document.getElementById('resultsSection').classList.add('show');
            document.getElementById('resultsSection').scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
    </script>
</body>
</html>
    """

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_resume(
    resume_file: UploadFile = File(...),
    job_description: str = Form("")
):
    """Analyze uploaded resume and return comprehensive ATS feedback"""
    
    # Validate file type
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    file_ext = resume_file.filename.lower().split('.')[-1]
    if file_ext not in ['pdf', 'docx', 'txt']:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload PDF, DOCX, or TXT files."
        )
    
    # Validate file size (10MB limit)
    if hasattr(resume_file, 'size') and resume_file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    try:
        # Read file bytes
        file_bytes = await resume_file.read()
        
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Extract text based on file type
        resume_text = ""
        if file_ext == 'pdf':
            resume_text = extract_text_from_pdf(file_bytes)
        elif file_ext == 'docx':
            resume_text = extract_text_from_docx(file_bytes)
        elif file_ext == 'txt':
            resume_text = extract_text_from_txt(file_bytes)
        
        # Validate extracted text
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400, 
                detail="Could not extract sufficient text from the file. Please ensure your resume contains readable text."
            )
        
        # Call AI service for analysis
        result = call_groq_ai(resume_text, job_description)
        
        return AnalysisResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing your resume: {str(e)}. Please try again."
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy", 
        "message": "AI ATS Resume Checker API is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "AI ATS Resume Checker API",
        "version": "1.0.0",
        "description": "Professional resume analysis with AI-powered ATS compatibility scoring",
        "supported_formats": ["PDF", "DOCX", "TXT"],
        "max_file_size": "10MB",
        "features": [
            "ATS Compatibility Scoring (0-100)",
            "Detailed Feedback Analysis",
            "Keyword Matching",
            "Improvement Recommendations",
            "Professional Formatting Assessment"
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

# For Vercel deployment - expose the app instance
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
