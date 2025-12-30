// ============================================
// ATS PRO - Interactive JavaScript
// ============================================

// DOM Elements
const fileUploadArea = document.getElementById('fileUploadArea');
const fileInput = document.getElementById('fileInput');
const selectedFile = document.getElementById('selectedFile');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFile = document.getElementById('removeFile');
const uploadForm = document.getElementById('uploadForm');
const loading = document.getElementById('loading');
const resultsSection = document.getElementById('resultsSection');
const analyzeBtn = document.getElementById('analyzeBtn');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');

// State
let selectedFileData = null;
let analysisInProgress = false;

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initAnimations();
    initStatCounters();
    initSmoothScrolling();
    initIntersectionObserver();
});

// ============================================
// Stat Counter Animation
// ============================================
function initStatCounters() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.dataset.target);
                animateCounter(entry.target, target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(num => observer.observe(num));
}

function animateCounter(element, target) {
    const duration = 2000;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (target - start) * easeOut);
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// ============================================
// Smooth Scrolling
// ============================================
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
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
}

// ============================================
// Intersection Observer for Animations
// ============================================
function initIntersectionObserver() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.feature-card, .step-card').forEach(el => {
        observer.observe(el);
    });
}

// ============================================
// General Animations
// ============================================
function initAnimations() {
    // Typewriter effect for hero title
    const typewriter = document.querySelector('.typewriter');
    if (typewriter) {
        const text = typewriter.textContent;
        typewriter.textContent = '';
        let i = 0;
        
        function type() {
            if (i < text.length) {
                typewriter.textContent += text.charAt(i);
                i++;
                setTimeout(type, 100);
            }
        }
        
        setTimeout(type, 500);
    }
}

// ============================================
// File Upload Handling
// ============================================

// Drag and drop
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
    const allowedTypes = [
        'application/pdf', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
        'text/plain'
    ];
    
    const extension = file.name.toLowerCase().split('.').pop();
    const validExtension = ['pdf', 'docx', 'txt'].includes(extension);
    
    if (!allowedTypes.includes(file.type) && !validExtension) {
        showNotification('Please select a PDF, DOCX, or TXT file.', 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showNotification('File size should not exceed 10MB.', 'error');
        return;
    }
    
    selectedFileData = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileUploadArea.style.display = 'none';
    selectedFile.classList.add('show');
    
    // Hide results if visible
    resultsSection.classList.remove('show');
    resultsSection.style.display = 'none';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Remove file
removeFile.addEventListener('click', () => {
    selectedFileData = null;
    fileInput.value = '';
    fileUploadArea.style.display = 'block';
    selectedFile.classList.remove('show');
    resultsSection.classList.remove('show');
    resultsSection.style.display = 'none';
});

// ============================================
// Form Submission & Analysis
// ============================================
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!selectedFileData) {
        showNotification('Please select a file to analyze.', 'error');
        return;
    }
    
    if (analysisInProgress) return;
    analysisInProgress = true;
    
    // Show loading state
    analyzeBtn.classList.add('loading');
    analyzeBtn.disabled = true;
    loading.classList.add('show');
    
    // Animate loading steps
    animateLoadingSteps();
    
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
            // Complete loading animation
            completeLoadingAnimation();
            
            // Wait for animation to finish
            setTimeout(() => {
                loading.classList.remove('show');
                displayResults(data);
            }, 500);
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error analyzing resume: ' + error.message, 'error');
        loading.classList.remove('show');
    } finally {
        analyzeBtn.classList.remove('loading');
        analyzeBtn.disabled = false;
        analysisInProgress = false;
    }
});

// Animate loading steps
function animateLoadingSteps() {
    const steps = document.querySelectorAll('.analysis-steps .step');
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.querySelector('.progress-text');
    
    const messages = [
        'Parsing document content...',
        'Running AI analysis...',
        'Calculating ATS metrics...',
        'Generating detailed report...'
    ];
    
    let currentStep = 0;
    progressFill.style.width = '0%';
    
    steps.forEach(step => {
        step.classList.remove('active', 'completed');
    });
    steps[0].classList.add('active');
    
    const interval = setInterval(() => {
        if (currentStep < steps.length - 1) {
            steps[currentStep].classList.remove('active');
            steps[currentStep].classList.add('completed');
            currentStep++;
            steps[currentStep].classList.add('active');
            progressFill.style.width = ((currentStep + 1) / steps.length * 100) + '%';
            progressText.textContent = messages[currentStep];
        }
    }, 1200);
    
    // Store interval for cleanup
    loading.dataset.intervalId = interval;
}

function completeLoadingAnimation() {
    const steps = document.querySelectorAll('.analysis-steps .step');
    const progressFill = document.querySelector('.progress-fill');
    
    // Clear interval
    if (loading.dataset.intervalId) {
        clearInterval(parseInt(loading.dataset.intervalId));
    }
    
    // Mark all steps as completed
    steps.forEach(step => {
        step.classList.remove('active');
        step.classList.add('completed');
    });
    
    progressFill.style.width = '100%';
}

// ============================================
// Display Results
// ============================================
function displayResults(data) {
    // Show results section
    resultsSection.style.display = 'block';
    setTimeout(() => {
        resultsSection.classList.add('show');
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
    
    // Animate main score
    animateScore(data.ats_score);
    
    // Update score badge and colors
    updateScoreVisuals(data.ats_score);
    
    // Update feedback
    document.getElementById('overallFeedback').textContent = data.overall_feedback;
    
    // Animate sub-scores
    animateSubScores(data);
    
    // Populate strengths
    populateList('strengthsList', data.strengths);
    
    // Populate improvements
    populateList('improvementsList', data.areas_for_improvement);
    
    // Populate keywords
    populateKeywords(data.keyword_analysis);
    
    // Populate recommendations
    populateRecommendations(data.recommendations);
    
    // Populate detailed metrics
    populateMetrics(data);
}

// Animate main score counter
function animateScore(targetScore) {
    const scoreElement = document.getElementById('atsScore');
    const scoreRing = document.getElementById('scoreRingProgress');
    
    // Animate number
    let currentScore = 0;
    const duration = 1500;
    const startTime = performance.now();
    
    function updateScore(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        currentScore = Math.floor(targetScore * easeOut);
        
        scoreElement.textContent = currentScore;
        
        // Update ring
        const circumference = 2 * Math.PI * 70;
        const offset = circumference - (currentScore / 100) * circumference;
        scoreRing.style.strokeDashoffset = offset;
        
        if (progress < 1) {
            requestAnimationFrame(updateScore);
        }
    }
    
    requestAnimationFrame(updateScore);
}

// Update score visuals based on score
function updateScoreVisuals(score) {
    const scoreBadge = document.getElementById('scoreBadge');
    const scoreGrade = document.getElementById('scoreGrade');
    const gradientStart = document.getElementById('gradientStart');
    const gradientEnd = document.getElementById('gradientEnd');
    
    let grade, colorStart, colorEnd;
    
    if (score >= 90) {
        grade = 'Exceptional';
        colorStart = '#10b981';
        colorEnd = '#34d399';
    } else if (score >= 80) {
        grade = 'Excellent';
        colorStart = '#0ea5e9';
        colorEnd = '#38bdf8';
    } else if (score >= 70) {
        grade = 'Very Good';
        colorStart = '#6366f1';
        colorEnd = '#818cf8';
    } else if (score >= 60) {
        grade = 'Good';
        colorStart = '#8b5cf6';
        colorEnd = '#a78bfa';
    } else if (score >= 50) {
        grade = 'Fair';
        colorStart = '#f59e0b';
        colorEnd = '#fbbf24';
    } else if (score >= 40) {
        grade = 'Needs Work';
        colorStart = '#f97316';
        colorEnd = '#fb923c';
    } else {
        grade = 'Critical';
        colorStart = '#ef4444';
        colorEnd = '#f87171';
    }
    
    scoreGrade.textContent = grade;
    scoreBadge.style.background = `linear-gradient(135deg, ${colorStart}, ${colorEnd})`;
    gradientStart.setAttribute('stop-color', colorStart);
    gradientEnd.setAttribute('stop-color', colorEnd);
}

// Animate sub-scores
function animateSubScores(data) {
    const scores = [
        { id: 'keywordScore', valueId: 'keywordValue', score: data.keyword_analysis?.keyword_score || 0 },
        { id: 'formattingScore', valueId: 'formattingValue', score: data.formatting_score || 0 },
        { id: 'contentScore', valueId: 'contentValue', score: data.content_quality_score || 0 },
        { id: 'impactScore', valueId: 'impactValue', score: data.impact_score || data.content_quality_score || 0 }
    ];
    
    scores.forEach((item, index) => {
        setTimeout(() => {
            const bar = document.getElementById(item.id);
            const value = document.getElementById(item.valueId);
            
            bar.style.width = item.score + '%';
            value.textContent = item.score + '%';
            
            // Add color class based on score
            bar.classList.remove('excellent', 'good', 'average', 'poor');
            if (item.score >= 80) bar.classList.add('excellent');
            else if (item.score >= 60) bar.classList.add('good');
            else if (item.score >= 40) bar.classList.add('average');
            else bar.classList.add('poor');
            
        }, index * 200);
    });
}

// Populate list items with animation
function populateList(listId, items) {
    const list = document.getElementById(listId);
    list.innerHTML = '';
    
    if (!items || items.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No data available';
        list.appendChild(li);
        return;
    }
    
    items.forEach((item, index) => {
        setTimeout(() => {
            const li = document.createElement('li');
            li.textContent = item;
            li.style.animationDelay = `${index * 0.1}s`;
            list.appendChild(li);
        }, index * 100);
    });
}

// Populate keywords
function populateKeywords(keywordAnalysis) {
    const presentContainer = document.getElementById('presentKeywords');
    const missingContainer = document.getElementById('missingKeywords');
    
    presentContainer.innerHTML = '';
    missingContainer.innerHTML = '';
    
    const presentKeywords = keywordAnalysis?.present_keywords || [];
    const missingKeywords = keywordAnalysis?.missing_keywords || [];
    
    if (presentKeywords.length === 0) {
        presentContainer.innerHTML = '<span style="opacity: 0.6">No keywords detected</span>';
    } else {
        presentKeywords.forEach((keyword, index) => {
            setTimeout(() => {
                const span = document.createElement('span');
                span.textContent = keyword;
                span.style.animationDelay = `${index * 0.05}s`;
                presentContainer.appendChild(span);
            }, index * 50);
        });
    }
    
    if (missingKeywords.length === 0) {
        missingContainer.innerHTML = '<span style="opacity: 0.6">All essential keywords present</span>';
    } else {
        missingKeywords.forEach((keyword, index) => {
            setTimeout(() => {
                const span = document.createElement('span');
                span.textContent = keyword;
                span.style.animationDelay = `${index * 0.05}s`;
                missingContainer.appendChild(span);
            }, index * 50);
        });
    }
}

// Populate recommendations
function populateRecommendations(recommendations) {
    const container = document.getElementById('recommendationsList');
    container.innerHTML = '';
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p style="color: var(--gray-400)">No recommendations at this time.</p>';
        return;
    }
    
    recommendations.forEach((rec, index) => {
        setTimeout(() => {
            const div = document.createElement('div');
            div.className = 'recommendation-item';
            div.style.animationDelay = `${index * 0.1}s`;
            div.innerHTML = `
                <span class="recommendation-number">${index + 1}</span>
                <span class="recommendation-text">${rec}</span>
            `;
            container.appendChild(div);
        }, index * 100);
    });
}

// Populate detailed metrics
function populateMetrics(data) {
    const container = document.getElementById('detailedMetrics');
    container.innerHTML = '';
    
    const metrics = [
        { icon: 'fas fa-key', label: 'Keywords Found', value: data.keyword_analysis?.present_keywords?.length || 0, color: 'gradient-1' },
        { icon: 'fas fa-chart-bar', label: 'Formatting Score', value: data.formatting_score || 0, suffix: '%', color: 'gradient-2' },
        { icon: 'fas fa-star', label: 'Content Quality', value: data.content_quality_score || 0, suffix: '%', color: 'gradient-3' },
        { icon: 'fas fa-bullseye', label: 'ATS Match Rate', value: data.ats_score || 0, suffix: '%', color: 'gradient-4' }
    ];
    
    metrics.forEach((metric, index) => {
        const div = document.createElement('div');
        div.className = 'metric-item';
        div.innerHTML = `
            <div class="metric-icon ${metric.color}">
                <i class="${metric.icon}"></i>
            </div>
            <div class="metric-value">${metric.value}${metric.suffix || ''}</div>
            <div class="metric-label">${metric.label}</div>
        `;
        container.appendChild(div);
    });
}

// ============================================
// New Analysis Button
// ============================================
newAnalysisBtn.addEventListener('click', () => {
    // Reset UI
    resultsSection.classList.remove('show');
    resultsSection.style.display = 'none';
    
    // Scroll to upload section
    document.getElementById('upload-section').scrollIntoView({ behavior: 'smooth' });
    
    // Reset file selection
    selectedFileData = null;
    fileInput.value = '';
    fileUploadArea.style.display = 'block';
    selectedFile.classList.remove('show');
    document.getElementById('jobDescription').value = '';
});

// ============================================
// Notification System
// ============================================
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Styles
    Object.assign(notification.style, {
        position: 'fixed',
        bottom: '2rem',
        right: '2rem',
        padding: '1rem 1.5rem',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        zIndex: '9999',
        animation: 'slideIn 0.3s ease',
        background: type === 'error' ? '#fef2f2' : type === 'success' ? '#f0fdf4' : '#eff6ff',
        color: type === 'error' ? '#dc2626' : type === 'success' ? '#16a34a' : '#2563eb',
        border: `1px solid ${type === 'error' ? '#fecaca' : type === 'success' ? '#bbf7d0' : '#bfdbfe'}`,
        boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
    });
    
    document.body.appendChild(notification);
    
    // Add animation keyframes
    if (!document.getElementById('notificationStyles')) {
        const style = document.createElement('style');
        style.id = 'notificationStyles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Auto remove
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// ============================================
// Parallax Effects
// ============================================
document.addEventListener('mousemove', (e) => {
    const shapes = document.querySelectorAll('.floating-shape');
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;
    
    shapes.forEach((shape, i) => {
        const speed = (i + 1) * 10;
        const xOffset = (x - 0.5) * speed;
        const yOffset = (y - 0.5) * speed;
        shape.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
    });
});
