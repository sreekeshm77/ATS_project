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

# Create the FastAPI app instance - Vercel will automatically detect this
app = FastAPI(title="AI ATS Resume Checker API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ResumeAnalysis(BaseModel):
    score: int
    feedback: str
    strengths: List[str]
    improvements: List[str]
    keywords_found: List[str]
    keywords_missing: List[str]

class JobDescription(BaseModel):
    content: str

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF content."""
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

def extract_text_from_docx(docx_content: bytes) -> str:
    """Extract text from DOCX content."""
    try:
        # Save bytes to a temporary file-like object
        docx_file = io.BytesIO(docx_content)
        text = docx2txt.process(docx_file)
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing DOCX: {str(e)}")

def analyze_resume_with_ai(resume_text: str, job_description: str = "") -> dict:
    """Use Groq AI to analyze the resume."""
    
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) and HR professional. Analyze the following resume and provide a comprehensive evaluation.

    Resume Content:
    {resume_text}

    Job Description (if provided):
    {job_description}

    Please provide your analysis in the following JSON format:
    {{
        "score": <integer from 0-100>,
        "feedback": "<comprehensive feedback about the resume>",
        "strengths": ["<strength1>", "<strength2>", "<strength3>"],
        "improvements": ["<improvement1>", "<improvement2>", "<improvement3>"],
        "keywords_found": ["<keyword1>", "<keyword2>", "<keyword3>"],
        "keywords_missing": ["<missing_keyword1>", "<missing_keyword2>"]
    }}

    Consider the following factors in your analysis:
    1. ATS compatibility (formatting, keywords, structure)
    2. Content quality and relevance
    3. Professional presentation
    4. Keyword optimization
    5. Completeness of information
    6. Alignment with job description (if provided)

    Provide specific, actionable feedback that will help improve the resume's effectiveness.
    """

    try:
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert ATS and HR professional. Provide detailed, actionable resume analysis in valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }

        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        ai_response = result['choices'][0]['message']['content']
        
        # Extract JSON from the response
        try:
            # Find JSON content between curly braces
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            json_str = ai_response[start_idx:end_idx]
            analysis = json.loads(json_str)
            
            # Ensure all required fields exist with defaults
            analysis.setdefault("score", 75)
            analysis.setdefault("feedback", "Resume analysis completed.")
            analysis.setdefault("strengths", [])
            analysis.setdefault("improvements", [])
            analysis.setdefault("keywords_found", [])
            analysis.setdefault("keywords_missing", [])
            
            return analysis
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "score": 75,
                "feedback": ai_response,
                "strengths": ["Professional experience included", "Educational background present"],
                "improvements": ["Add more specific achievements", "Include relevant keywords"],
                "keywords_found": [],
                "keywords_missing": []
            }
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# HTML template for the frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI ATS Resume Checker</title>
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
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            padding: 40px;
        }
        
        .upload-section {
            margin-bottom: 40px;
        }
        
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 15px;
            padding: 60px 20px;
            text-align: center;
            background: #fafafa;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area.dragover {
            border-color: #4facfe;
            background: #f0f9ff;
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 4em;
            color: #4facfe;
            margin-bottom: 20px;
        }
        
        .upload-text {
            font-size: 1.3em;
            color: #666;
            margin-bottom: 20px;
        }
        
        .file-input {
            display: none;
        }
        
        .upload-btn {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1.1em;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .upload-btn:hover {
            transform: translateY(-2px);
        }
        
        .job-description {
            margin-bottom: 30px;
        }
        
        .job-description textarea {
            width: 100%;
            min-height: 150px;
            padding: 20px;
            border: 2px solid #ddd;
            border-radius: 15px;
            font-size: 1em;
            resize: vertical;
            font-family: inherit;
        }
        
        .job-description textarea:focus {
            outline: none;
            border-color: #4facfe;
        }
        
        .analyze-btn {
            background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 50px;
            font-size: 1.2em;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 30px;
        }
        
        .analyze-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(255,107,107,0.3);
        }
        
        .analyze-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #4facfe;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .results {
            display: none;
            margin-top: 40px;
        }
        
        .score-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .score-number {
            font-size: 4em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .score-label {
            font-size: 1.3em;
            opacity: 0.9;
        }
        
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .analysis-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            border: 1px solid #eee;
        }
        
        .analysis-card h3 {
            color: #4facfe;
            margin-bottom: 20px;
            font-size: 1.4em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .analysis-card ul {
            list-style: none;
            padding: 0;
        }
        
        .analysis-card li {
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
            position: relative;
            padding-left: 25px;
        }
        
        .analysis-card li:before {
            content: "•";
            color: #4facfe;
            font-weight: bold;
            position: absolute;
            left: 0;
        }
        
        .feedback-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
        }
        
        .feedback-section h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.4em;
        }
        
        .feedback-text {
            line-height: 1.6;
            color: #555;
            font-size: 1.1em;
        }
        
        .error {
            background: #ffe6e6;
            border: 1px solid #ffcccc;
            color: #cc0000;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 15px;
            }
            
            .header {
                padding: 30px 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .main-content {
                padding: 20px;
            }
            
            .upload-area {
                padding: 40px 20px;
            }
            
            .analysis-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI ATS Resume Checker</h1>
            <p>Get instant feedback on your resume's ATS compatibility and effectiveness</p>
        </div>
        
        <div class="main-content">
            <div class="upload-section">
                <h2>📄 Upload Your Resume</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <div class="upload-text">Drag & drop your resume here or click to browse</div>
                    <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                        Choose File
                    </button>
                    <input type="file" id="fileInput" class="file-input" accept=".pdf,.docx,.txt">
                </div>
                <div id="fileName" style="margin-top: 15px; color: #4facfe; font-weight: bold;"></div>
            </div>
            
            <div class="job-description">
                <h2>💼 Job Description (Optional)</h2>
                <textarea id="jobDescription" placeholder="Paste the job description here to get more targeted feedback..."></textarea>
            </div>
            
            <button class="analyze-btn" id="analyzeBtn" onclick="analyzeResume()" disabled>
                🔍 Analyze Resume
            </button>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Analyzing your resume with AI... This may take a few moments.</p>
            </div>
            
            <div class="results" id="results">
                <div class="score-card">
                    <div class="score-number" id="scoreNumber">85</div>
                    <div class="score-label">ATS Compatibility Score</div>
                </div>
                
                <div class="feedback-section">
                    <h3>📝 Overall Feedback</h3>
                    <div class="feedback-text" id="feedbackText"></div>
                </div>
                
                <div class="analysis-grid">
                    <div class="analysis-card">
                        <h3>✅ Strengths</h3>
                        <ul id="strengthsList"></ul>
                    </div>
                    
                    <div class="analysis-card">
                        <h3>🎯 Areas for Improvement</h3>
                        <ul id="improvementsList"></ul>
                    </div>
                    
                    <div class="analysis-card">
                        <h3>🔍 Keywords Found</h3>
                        <ul id="keywordsFoundList"></ul>
                    </div>
                    
                    <div class="analysis-card">
                        <h3>❌ Missing Keywords</h3>
                        <ul id="keywordsMissingList"></ul>
                    </div>
                </div>
            </div>
            
            <div id="error" class="error" style="display: none;"></div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        
        // File upload handling
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const analyzeBtn = document.getElementById('analyzeBtn');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
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
            const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
            
            if (!allowedTypes.includes(file.type)) {
                showError('Please select a PDF, DOCX, or TXT file.');
                return;
            }
            
            selectedFile = file;
            fileName.textContent = `Selected: ${file.name}`;
            analyzeBtn.disabled = false;
            hideError();
        }
        
        async function analyzeResume() {
            if (!selectedFile) {
                showError('Please select a resume file first.');
                return;
            }
            
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            loading.style.display = 'block';
            results.style.display = 'none';
            analyzeBtn.disabled = true;
            hideError();
            
            try {
                const formData = new FormData();
                formData.append('file', selectedFile);
                
                const jobDescription = document.getElementById('jobDescription').value.trim();
                if (jobDescription) {
                    formData.append('job_description', jobDescription);
                }
                
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Analysis failed');
                }
                
                const analysis = await response.json();
                displayResults(analysis);
                
            } catch (error) {
                showError(error.message || 'An error occurred while analyzing your resume.');
            } finally {
                loading.style.display = 'none';
                analyzeBtn.disabled = false;
            }
        }
        
        function displayResults(analysis) {
            document.getElementById('scoreNumber').textContent = analysis.score;
            document.getElementById('feedbackText').textContent = analysis.feedback;
            
            populateList('strengthsList', analysis.strengths);
            populateList('improvementsList', analysis.improvements);
            populateList('keywordsFoundList', analysis.keywords_found);
            populateList('keywordsMissingList', analysis.keywords_missing);
            
            document.getElementById('results').style.display = 'block';
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        }
        
        function populateList(elementId, items) {
            const list = document.getElementById(elementId);
            list.innerHTML = '';
            
            if (items && items.length > 0) {
                items.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = item;
                    list.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'None identified';
                li.style.fontStyle = 'italic';
                li.style.color = '#999';
                list.appendChild(li);
            }
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            errorDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the HTML interface."""
    return HTMLResponse(content=HTML_TEMPLATE)

@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(default="")
):
    """Analyze uploaded resume file."""
    
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="AI service configuration error")
    
    # Check file type and size
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
    
    # Read file content
    file_content = await file.read()
    
    # Extract text based on file type
    if file.filename.lower().endswith('.pdf'):
        resume_text = extract_text_from_pdf(file_content)
    elif file.filename.lower().endswith('.docx'):
        resume_text = extract_text_from_docx(file_content)
    elif file.filename.lower().endswith('.txt'):
        resume_text = file_content.decode('utf-8')
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, DOCX, or TXT files.")
    
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the file")
    
    # Analyze with AI
    try:
        analysis = analyze_resume_with_ai(resume_text, job_description or "")
        return JSONResponse(content=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
