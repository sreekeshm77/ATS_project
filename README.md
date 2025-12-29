# 🚀 AI ATS Resume Checker

A professional AI-powered ATS (Applicant Tracking System) resume checker that provides comprehensive feedback and scoring to help job seekers optimize their resumes for better visibility in recruitment processes.

## ✨ Features

### � Comprehensive Analysis
- **ATS Score (0-100)**: Overall compatibility rating
- **Detailed Feedback**: Section-by-section analysis including:
  - Summary/Objective assessment
  - Skills evaluation
  - Experience review
  - Education analysis
  - Formatting review

### 🎯 Smart Recommendations
- **Keyword Optimization**: Identifies matched and missing keywords
- **Improvement Suggestions**: Actionable recommendations
- **Strengths & Weaknesses**: Clear pros and cons analysis
- **Job-Specific Feedback**: Enhanced analysis when job description is provided

### 💻 Modern Interface
- **Drag & Drop Upload**: Support for PDF, DOCX, and TXT files
- **Responsive Design**: Works perfectly on all devices
- **Beautiful UI**: Professional and intuitive interface
- **Real-time Feedback**: Instant analysis results

### 🔒 Secure & Fast
- **File Size Limit**: Up to 10MB per file
- **Privacy Focused**: Files are processed temporarily and not stored
- **Fast Processing**: Powered by Groq's Llama 3 AI model

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **AI Engine**: Groq API with Llama 3-70B model
- **File Processing**: PyMuPDF (PDF), docx2txt (DOCX)
- **Frontend**: Modern HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with responsive design
- **Deployment**: Vercel (serverless)

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Groq API key ([Get one here](https://console.groq.com/))

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-ats-resume-checker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   ```

4. **Run the application**
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open your browser**
   Navigate to `http://localhost:8000`

## 🌐 Deployment on Vercel

### Automatic Deployment
1. Fork this repository
2. Connect your GitHub account to Vercel
3. Import your forked repository
4. Add environment variable: `GROQ_API_KEY=your_actual_api_key`
5. Deploy!

### Manual Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variable
vercel env add GROQ_API_KEY
```

## 📁 Project Structure

```
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel deployment configuration
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```

## 🔧 API Endpoints

### Main Endpoints
- `GET /` - Main application interface (HTML)
- `POST /analyze` - Resume analysis endpoint
- `GET /health` - Health check endpoint
- `GET /api/info` - API information endpoint

### Analysis Request
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "resume_file=@your_resume.pdf" \
  -F "job_description=Your job description here"
```

### Response Format
```json
{
  "ats_score": 85,
  "summary_feedback": "...",
  "skills_feedback": "...",
  "experience_feedback": "...",
  "education_feedback": "...",
  "formatting_feedback": "...",
  "pros": ["..."],
  "cons": ["..."],
  "recommendations": ["..."],
  "matched_keywords": ["..."],
  "missing_keywords": ["..."],
  "improvement_areas": ["..."],
  "strengths": ["..."]
}
```

## 🎨 Features Breakdown

### File Support
- **PDF**: Extracts text using PyMuPDF
- **DOCX**: Processes Word documents with docx2txt
- **TXT**: Direct text file processing

### AI Analysis
- **Comprehensive Scoring**: 0-100 scale based on ATS best practices
- **Contextual Feedback**: Tailored advice based on resume content
- **Job Matching**: Enhanced analysis when job description is provided
- **Industry Standards**: Follows current ATS and recruitment trends

### User Experience
- **Progressive Enhancement**: Works without JavaScript (basic functionality)
- **Error Handling**: Comprehensive error messages and recovery
- **Loading States**: Clear feedback during processing
- **Mobile Optimized**: Fully responsive design

## ⚙️ Configuration

### Environment Variables
```bash
GROQ_API_KEY=your_groq_api_key_here  # Required: Groq API authentication
```

### File Limits
- **Maximum file size**: 10MB
- **Supported formats**: PDF, DOCX, TXT
- **Minimum content**: 50 characters of extractable text

## 🔍 How It Works

1. **File Upload**: User uploads resume in supported format
2. **Text Extraction**: Application extracts text based on file type
3. **AI Analysis**: Groq's Llama 3 model analyzes content
4. **Scoring Algorithm**: Comprehensive scoring based on ATS criteria
5. **Feedback Generation**: Detailed recommendations and insights
6. **Results Display**: Beautiful, easy-to-understand results

## 📊 Scoring Criteria

The ATS score is calculated based on:
- **Keyword Optimization** (25%)
- **Structure and Formatting** (20%)
- **Content Quality** (20%)
- **Professional Presentation** (15%)
- **Completeness** (10%)
- **ATS Compatibility** (10%)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed description
3. Include error messages and steps to reproduce

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for providing the AI infrastructure
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Vercel](https://vercel.com/) for seamless deployment platform

---

## 📈 Roadmap

- [ ] Multiple language support
- [ ] Resume template suggestions
- [ ] Industry-specific analysis
- [ ] Bulk resume processing
- [ ] Integration with job boards
- [ ] Resume builder tool
- [ ] Advanced analytics dashboard

---

**Made with ❤️ for job seekers everywhere**
