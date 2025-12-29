# ATS Resume Checker

An AI-powered Applicant Tracking System (ATS) checker that analyzes resumes and provides comprehensive feedback with scores out of 100.

## Features

- **AI-Powered Analysis**: Uses Groq API with Mixtral-8x7B model for intelligent resume analysis
- **ATS Score**: Get a comprehensive score out of 100 for your resume
- **Detailed Feedback**: Receive actionable insights including:
  - Strengths and areas for improvement
  - Keyword analysis (present and missing keywords)
  - Content quality assessment
  - Formatting recommendations
- **Multiple File Formats**: Supports PDF, DOCX, and TXT files
- **Job Description Matching**: Optional job description input for targeted analysis
- **Beautiful UI**: Modern purple and white themed interface
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI Model**: Groq API with Mixtral-8x7B-32768
- **File Processing**: PyPDF2, python-docx
- **Deployment**: Vercel

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd ats-resume-checker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file and add your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
```

4. Run the application:
```bash
python main.py
```

The app will be available at `http://localhost:8000`

## Deployment on Vercel

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
vercel
```

4. Set environment variable in Vercel dashboard:
   - Go to your project settings
   - Add `GROQ_API_KEY` with your API key value

## Usage

1. Visit the application URL
2. Upload your resume (PDF, DOCX, or TXT format)
3. Optionally paste a job description for targeted analysis
4. Click "Analyze Resume"
5. Review your ATS score and detailed feedback
6. Implement the recommendations to improve your resume

## API Endpoints

- `GET /`: Main application page
- `POST /analyze`: Analyze uploaded resume
- `GET /health`: Health check endpoint

## Features Breakdown

### ATS Score Components
- **Keyword Analysis**: Matches relevant keywords for the role
- **Formatting Score**: Evaluates ATS-friendly formatting
- **Content Quality**: Assesses overall content quality and relevance

### Analysis Output
- Overall ATS score (0-100)
- Detailed strengths
- Areas for improvement
- Keyword analysis (present vs missing)
- Actionable recommendations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Support

For support or questions, please open an issue in the repository.
