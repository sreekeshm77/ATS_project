// DOM Elements
const fileUploadArea = document.getElementById('fileUploadArea');
const fileInput = document.getElementById('fileInput');
const selectedFile = document.getElementById('selectedFile');
const fileName = document.getElementById('fileName');
const removeFile = document.getElementById('removeFile');
const uploadForm = document.getElementById('uploadForm');
const loading = document.getElementById('loading');
const resultsSection = document.getElementById('resultsSection');
const analyzeBtn = document.getElementById('analyzeBtn');

// File upload handling
let selectedFileData = null;

// Drag and drop functionality
fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('drag-over');
});

fileUploadArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('drag-over');
});

fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelection(files[0]);
    }
});

// File input change
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
    }
});

// Handle file selection
function handleFileSelection(file) {
    // Check file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.docx') && !file.name.toLowerCase().endsWith('.txt')) {
        alert('Please select a PDF, DOCX, or TXT file.');
        return;
    }
    
    // Check file size (limit to 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size should not exceed 10MB.');
        return;
    }
    
    selectedFileData = file;
    fileName.textContent = file.name;
    fileUploadArea.style.display = 'none';
    selectedFile.style.display = 'flex';
}

// Remove file
removeFile.addEventListener('click', () => {
    selectedFileData = null;
    fileInput.value = '';
    fileUploadArea.style.display = 'block';
    selectedFile.style.display = 'none';
    resultsSection.style.display = 'none';
});

// Form submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!selectedFileData) {
        alert('Please select a file to analyze.');
        return;
    }
    
    // Show loading
    loading.style.display = 'block';
    resultsSection.style.display = 'none';
    analyzeBtn.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFileData);
        formData.append('job_description', document.getElementById('jobDescription').value);
        
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayResults(data);
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error analyzing resume: ' + error.message);
    } finally {
        loading.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

// Display results
function displayResults(data) {
    // Update main score
    document.getElementById('atsScore').textContent = data.ats_score;
    document.getElementById('overallFeedback').textContent = data.overall_feedback;
    
    // Update sub-scores with animation
    setTimeout(() => {
        document.getElementById('keywordScore').style.width = data.keyword_analysis.keyword_score + '%';
        document.getElementById('formattingScore').style.width = data.formatting_score + '%';
        document.getElementById('contentScore').style.width = data.content_quality_score + '%';
    }, 500);
    
    // Update strengths
    const strengthsList = document.getElementById('strengthsList');
    strengthsList.innerHTML = '';
    data.strengths.forEach(strength => {
        const li = document.createElement('li');
        li.textContent = strength;
        strengthsList.appendChild(li);
    });
    
    // Update improvements
    const improvementsList = document.getElementById('improvementsList');
    improvementsList.innerHTML = '';
    data.areas_for_improvement.forEach(improvement => {
        const li = document.createElement('li');
        li.textContent = improvement;
        improvementsList.appendChild(li);
    });
    
    // Update keywords
    const presentKeywords = document.getElementById('presentKeywords');
    presentKeywords.innerHTML = '';
    data.keyword_analysis.present_keywords.forEach(keyword => {
        const span = document.createElement('span');
        span.textContent = keyword;
        presentKeywords.appendChild(span);
    });
    
    const missingKeywords = document.getElementById('missingKeywords');
    missingKeywords.innerHTML = '';
    data.keyword_analysis.missing_keywords.forEach(keyword => {
        const span = document.createElement('span');
        span.textContent = keyword;
        missingKeywords.appendChild(span);
    });
    
    // Update recommendations
    const recommendationsList = document.getElementById('recommendationsList');
    recommendationsList.innerHTML = '';
    data.recommendations.forEach(recommendation => {
        const li = document.createElement('li');
        li.textContent = recommendation;
        recommendationsList.appendChild(li);
    });
    
    // Show results with animation
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Update score circle color based on score
    const scoreCircle = document.querySelector('.score-circle');
    const score = data.ats_score;
    
    if (score >= 80) {
        scoreCircle.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    } else if (score >= 60) {
        scoreCircle.style.background = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';
    } else {
        scoreCircle.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
    }
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add some interactive elements
document.addEventListener('DOMContentLoaded', () => {
    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature, .sample-card, .detail-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
});
