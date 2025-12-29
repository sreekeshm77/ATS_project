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
    // Update main score with animation
    const scoreElement = document.getElementById('atsScore');
    const scoreCircle = document.querySelector('.score-circle');
    
    // Animate score counting
    let currentScore = 0;
    const targetScore = data.ats_score;
    const increment = targetScore / 50; // 50 steps for smooth animation
    
    const scoreInterval = setInterval(() => {
        currentScore += increment;
        if (currentScore >= targetScore) {
            currentScore = targetScore;
            clearInterval(scoreInterval);
        }
        scoreElement.textContent = Math.round(currentScore);
    }, 20);
    
    // Update overall feedback
    document.getElementById('overallFeedback').textContent = data.overall_feedback;
    
    // Update score circle color and border based on score
    setTimeout(() => {
        const score = data.ats_score;
        let circleColor, borderColor;
        
        if (score >= 85) {
            circleColor = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            borderColor = '#10b981';
        } else if (score >= 75) {
            circleColor = 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)';
            borderColor = '#3b82f6';
        } else if (score >= 60) {
            circleColor = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';
            borderColor = '#f59e0b';
        } else {
            circleColor = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
            borderColor = '#ef4444';
        }
        
        scoreCircle.style.background = circleColor;
        scoreCircle.style.borderColor = borderColor;
    }, 1000);
    
    // Update sub-scores with staggered animation
    setTimeout(() => {
        const keywordBar = document.getElementById('keywordScore');
        const formattingBar = document.getElementById('formattingScore');
        const contentBar = document.getElementById('contentScore');
        
        keywordBar.style.width = '0%';
        formattingBar.style.width = '0%';
        contentBar.style.width = '0%';
        
        setTimeout(() => keywordBar.style.width = data.keyword_analysis.keyword_score + '%', 100);
        setTimeout(() => formattingBar.style.width = data.formatting_score + '%', 300);
        setTimeout(() => contentBar.style.width = data.content_quality_score + '%', 500);
        
        // Add score labels
        setTimeout(() => {
            keywordBar.setAttribute('data-score', data.keyword_analysis.keyword_score + '%');
            formattingBar.setAttribute('data-score', data.formatting_score + '%');
            contentBar.setAttribute('data-score', data.content_quality_score + '%');
        }, 1000);
    }, 500);
    
    // Update strengths with staggered reveal
    const strengthsList = document.getElementById('strengthsList');
    strengthsList.innerHTML = '';
    data.strengths.forEach((strength, index) => {
        setTimeout(() => {
            const li = document.createElement('li');
            li.textContent = strength;
            li.style.opacity = '0';
            li.style.transform = 'translateX(-20px)';
            strengthsList.appendChild(li);
            
            // Animate in
            setTimeout(() => {
                li.style.transition = 'all 0.3s ease';
                li.style.opacity = '1';
                li.style.transform = 'translateX(0)';
            }, 50);
        }, index * 100);
    });
    
    // Update improvements with staggered reveal
    const improvementsList = document.getElementById('improvementsList');
    improvementsList.innerHTML = '';
    data.areas_for_improvement.forEach((improvement, index) => {
        setTimeout(() => {
            const li = document.createElement('li');
            li.textContent = improvement;
            li.style.opacity = '0';
            li.style.transform = 'translateX(-20px)';
            improvementsList.appendChild(li);
            
            // Animate in
            setTimeout(() => {
                li.style.transition = 'all 0.3s ease';
                li.style.opacity = '1';
                li.style.transform = 'translateX(0)';
            }, 50);
        }, index * 100);
    });
    
    // Update keywords with improved display
    const presentKeywords = document.getElementById('presentKeywords');
    presentKeywords.innerHTML = '';
    if (data.keyword_analysis.present_keywords && data.keyword_analysis.present_keywords.length > 0) {
        data.keyword_analysis.present_keywords.forEach((keyword, index) => {
            setTimeout(() => {
                const span = document.createElement('span');
                span.textContent = keyword;
                span.style.opacity = '0';
                span.style.transform = 'scale(0.8)';
                presentKeywords.appendChild(span);
                
                // Animate in
                setTimeout(() => {
                    span.style.transition = 'all 0.3s ease';
                    span.style.opacity = '1';
                    span.style.transform = 'scale(1)';
                }, 50);
            }, index * 50);
        });
    } else {
        presentKeywords.innerHTML = '<span style="opacity: 0.6; font-style: italic;">No keywords detected</span>';
    }
    
    const missingKeywords = document.getElementById('missingKeywords');
    missingKeywords.innerHTML = '';
    if (data.keyword_analysis.missing_keywords && data.keyword_analysis.missing_keywords.length > 0) {
        data.keyword_analysis.missing_keywords.forEach((keyword, index) => {
            setTimeout(() => {
                const span = document.createElement('span');
                span.textContent = keyword;
                span.style.opacity = '0';
                span.style.transform = 'scale(0.8)';
                missingKeywords.appendChild(span);
                
                // Animate in
                setTimeout(() => {
                    span.style.transition = 'all 0.3s ease';
                    span.style.opacity = '1';
                    span.style.transform = 'scale(1)';
                }, 50);
            }, index * 50);
        });
    } else {
        missingKeywords.innerHTML = '<span style="opacity: 0.6; font-style: italic;">All keywords present</span>';
    }
    
    // Update recommendations with staggered reveal
    const recommendationsList = document.getElementById('recommendationsList');
    recommendationsList.innerHTML = '';
    data.recommendations.forEach((recommendation, index) => {
        setTimeout(() => {
            const li = document.createElement('li');
            li.textContent = recommendation;
            li.style.opacity = '0';
            li.style.transform = 'translateX(-20px)';
            recommendationsList.appendChild(li);
            
            // Animate in
            setTimeout(() => {
                li.style.transition = 'all 0.3s ease';
                li.style.opacity = '1';
                li.style.transform = 'translateX(0)';
            }, 50);
        }, index * 100);
    });
    
    // Show results with animation
    resultsSection.style.display = 'block';
    resultsSection.style.opacity = '0';
    resultsSection.style.transform = 'translateY(30px)';
    
    setTimeout(() => {
        resultsSection.style.transition = 'all 0.5s ease';
        resultsSection.style.opacity = '1';
        resultsSection.style.transform = 'translateY(0)';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
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
