# AI ATS Resume Checker

A modern AI-powered ATS (Applicant Tracking System) resume checker built with FastAPI and a beautiful frontend interface.

## Features

- 📄 Upload resumes in PDF, DOCX, or JSON format
- 🤖 AI-powered analysis using Groq's Llama 3 model
- 📊 Detailed feedback on:
  - ATS Score (0-100)
  - Summary, Skills, Experience, and Education feedback
  - Strengths and areas for improvement
  - Actionable recommendations
  - Keyword matching analysis
- 💼 Optional job description comparison
- 🎨 Modern, responsive UI with drag-and-drop file upload
- ⚡ Fast API responses with proper error handling

## Tech Stack

- **Backend**: FastAPI, Python
- **AI**: Groq API (Llama 3-70B model)
- **File Processing**: PyMuPDF (PDF), docx2txt (DOCX)
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Deployment**: Vercel

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
4. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

## Deployment

This app is configured for deployment on Vercel:

1. Connect your GitHub repository to Vercel
2. Add your `GROQ_API_KEY` as an environment variable in Vercel
3. Deploy!

## API Endpoints

- `GET /` - Main application interface
- `POST /analyze` - Resume analysis endpoint
- `GET /health` - Health check endpoint

## Usage

1. Visit the application URL
2. Upload your resume (PDF, DOCX, or JSON)
3. Optionally paste a job description for better analysis
4. Click "Analyze Resume"
5. Get detailed AI feedback and recommendations

## Environment Variables

- `GROQ_API_KEY` - Your Groq API key (required)

## License

MIT License
