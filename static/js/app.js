// Application State
const state = {
    currentPage: 'input',
    workflowId: null,
    workflowState: null,
    results: null,
    retryCount: 0
};

// API Base URL
const API_BASE = window.location.origin;

// Utility Functions
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    state.currentPage = pageId;
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

function hideError() {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// Character Counters
function setupCharCounters() {
    ['jd', 'resume', 'projects'].forEach(id => {
        const textarea = document.getElementById(`${id}-text`);
        const counter = document.getElementById(`${id}-count`);
        if (textarea && counter) {
            textarea.addEventListener('input', () => {
                counter.textContent = textarea.value.length;
            });
        }
    });
}

// PDF Upload Setup
function setupPDFUpload() {
    const uploadArea = document.getElementById('resume-upload-area');
    const fileInput = document.getElementById('resume-pdf-input');
    const uploadBtn = document.getElementById('resume-upload-btn');
    const textToggle = document.getElementById('resume-text-toggle');
    const textSection = document.getElementById('resume-text-section');
    const fileName = document.getElementById('resume-file-name');
    const loadingIndicator = document.getElementById('resume-upload-loading');
    const resumeTextarea = document.getElementById('resume-text');

    // Click to upload
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        if (uploadBtn) {
            uploadBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }
    }

    // Drag and drop
    if (uploadArea) {
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
            if (files.length > 0 && files[0].type === 'application/pdf') {
                handlePDFUpload(files[0]);
            } else {
                showError('Please upload a PDF file');
            }
        });
    }

    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file && file.type === 'application/pdf') {
                handlePDFUpload(file);
            } else {
                showError('Please select a PDF file');
            }
        });
    }

    // Toggle text input
    if (textToggle) {
        textToggle.addEventListener('click', () => {
            textSection.style.display = textSection.style.display === 'none' ? 'block' : 'none';
            if (textSection.style.display === 'block') {
                uploadArea.style.display = 'none';
                if (uploadBtn) uploadBtn.parentElement.style.display = 'none';
            } else {
                uploadArea.style.display = 'block';
                if (uploadBtn) uploadBtn.parentElement.style.display = 'flex';
            }
        });
    }

    // Handle PDF upload
    async function handlePDFUpload(file) {
        if (!file) return;

        // Show loading
        loadingIndicator.style.display = 'flex';
        fileName.style.display = 'none';
        hideError();

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE}/api/v1/upload/resume-pdf`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to upload PDF');
            }

            const data = await response.json();
            
            // Set extracted text to textarea
            if (resumeTextarea) {
                resumeTextarea.value = data.extracted_text;
                // Trigger character count update
                const event = new Event('input', { bubbles: true });
                resumeTextarea.dispatchEvent(event);
            }

            // Show file name
            fileName.textContent = `✓ ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            fileName.style.display = 'block';
            fileName.style.color = '#10b981';

            // Hide upload area, show text section
            uploadArea.style.display = 'none';
            if (uploadBtn) uploadBtn.parentElement.style.display = 'none';
            textSection.style.display = 'block';

        } catch (error) {
            showError(error.message || 'Failed to process PDF');
            fileName.style.display = 'none';
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }
}

// Form Submission
async function handleFormSubmit(e) {
    e.preventDefault();
    hideError();

    const jdText = document.getElementById('jd-text').value.trim();
    const resumeText = document.getElementById('resume-text').value.trim();
    const projectsText = document.getElementById('projects-text').value.trim();

    if (!jdText) {
        showError('Please fill in the Job Description field');
        return;
    }

    if (!resumeText) {
        showError('Please upload a PDF resume or paste your resume text');
        return;
    }

    // Disable submit button
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Starting...</span>';

    try {
        // Start workflow
        const response = await fetch(`${API_BASE}/api/v1/workflow/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jd_text: jdText,
                resume_text: resumeText,
                projects_text: projectsText || undefined
            })
        });

        if (!response.ok) {
            throw new Error('Failed to start workflow');
        }

        const data = await response.json();
        state.workflowId = data.workflow_id;

        // Show loading page
        showPage('loading');
        updateLoadingState({
            status: 'running',
            progress: 0,
            message: 'Starting workflow...',
            current_step: 'agent1'
        });

        // Reset poll counter
        pollCount = 0;
        
        // Start polling for progress
        pollWorkflowProgress();

    } catch (error) {
        showError(error.message || 'Failed to start workflow');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Start Analysis</span>';
    }
}

// Poll Workflow Progress
let pollCount = 0;
const MAX_POLL_COUNT = 300; // 10 minutes max (300 * 2 seconds)

async function pollWorkflowProgress() {
    if (!state.workflowId) {
        console.error('No workflow ID available');
        return;
    }

    pollCount++;
    if (pollCount > MAX_POLL_COUNT) {
        showError('Workflow is taking too long. Please try again.');
        const retryBtn = document.getElementById('retry-btn');
        if (retryBtn) retryBtn.style.display = 'block';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/v1/workflow/progress/${state.workflowId}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                showError('Workflow not found. Please start again.');
                return;
            }
            throw new Error(`HTTP ${response.status}: Failed to get progress`);
        }

        const data = await response.json();
        console.log('Progress update:', data); // Debug log
        
        state.workflowState = data;

        updateLoadingState(data);

        if (data.status === 'completed') {
            pollCount = 0; // Reset counter
            // Load results
            try {
                const resultResponse = await fetch(`${API_BASE}/api/v1/workflow/result/${state.workflowId}`);
                if (!resultResponse.ok) {
                    throw new Error('Failed to get results');
                }
                const resultData = await resultResponse.json();
                state.results = resultData.results;

                // Show dashboard
                setTimeout(() => {
                    showPage('dashboard');
                    renderDashboard();
                }, 1000);
            } catch (error) {
                console.error('Error loading results:', error);
                showError('Workflow completed but failed to load results. Please refresh the page.');
            }
        } else if (data.status === 'failed') {
            pollCount = 0; // Reset counter
            // Show error and retry button
            const retryBtn = document.getElementById('retry-btn');
            if (retryBtn) retryBtn.style.display = 'block';
            
            const errorDiv = document.getElementById('loading-error');
            if (errorDiv && data.error) {
                errorDiv.textContent = `Error: ${data.error}`;
                errorDiv.style.display = 'block';
            }
        } else if (data.status === 'running') {
            // Continue polling
            setTimeout(pollWorkflowProgress, 2000);
        } else {
            // Unknown status, continue polling
            console.warn('Unknown workflow status:', data.status);
            setTimeout(pollWorkflowProgress, 2000);
        }
    } catch (error) {
        console.error('Progress polling error:', error);
        // Continue polling even on error (network issues might be temporary)
        if (pollCount < MAX_POLL_COUNT) {
            setTimeout(pollWorkflowProgress, 2000);
        } else {
            showError('Failed to get workflow progress. Please check your connection and try again.');
        }
    }
}

// Update Loading State
function updateLoadingState(data) {
    const titleEl = document.getElementById('loading-title');
    const stepEl = document.getElementById('loading-step');
    const messageEl = document.getElementById('loading-message');
    const progressFill = document.getElementById('progress-fill');
    const iconEl = document.getElementById('loading-icon');

    if (data.status === 'completed') {
        titleEl.textContent = 'Analysis Complete!';
        iconEl.innerHTML = '<svg class="spinner" style="color: #10b981;" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10" stroke-width="2"></circle><path d="M9 12l2 2 4-4"></path></svg>';
    } else if (data.status === 'failed') {
        titleEl.textContent = 'Processing Failed';
        iconEl.innerHTML = '<svg class="spinner" style="color: #ef4444;" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10" stroke-width="2"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
        if (data.error) {
            document.getElementById('loading-error').textContent = data.error;
            document.getElementById('loading-error').style.display = 'block';
        }
    }

    const stepNames = {
        'agent1': 'Input Validation',
        'agent2': 'JD Analysis',
        'agent3': 'Project Packaging',
        'agent4': 'Resume Optimization'
    };

    stepEl.textContent = stepNames[data.current_step] || data.current_step;
    messageEl.textContent = data.message || '';
    progressFill.style.width = `${data.progress || 0}%`;
}

// Render Dashboard
function renderDashboard() {
    if (!state.results) return;

    // Setup tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const tab = btn.dataset.tab;
            renderTab(tab);
        });
    });

    // Show action panel for resume tab
    const resumeBtn = document.querySelector('[data-tab="resume"]');
    if (resumeBtn) {
        resumeBtn.addEventListener('click', () => {
            document.getElementById('action-panel').style.display = 'block';
        });
    }

    // Render default tab (match)
    renderTab('match');
}

// Render Tab Content
function renderTab(tabName) {
    const contentEl = document.getElementById('tab-content');
    if (!contentEl || !state.results) return;

    const agent2 = state.results.agent2 || {};
    const agent3 = state.results.agent3 || {};
    const agent4 = state.results.agent4 || {};

    let html = '';

    switch(tabName) {
        case 'match':
            html = renderMatchAnalysis(agent2);
            break;
        case 'profile':
            html = renderCandidateProfile(agent2);
            break;
        case 'scenario':
            html = renderWorkScenario(agent2);
            break;
        case 'projects':
            html = renderProjects(agent3);
            break;
        case 'resume':
            html = renderResumeOptimization(agent4);
            break;
    }

    contentEl.innerHTML = html;
}

// Render Match Analysis
function renderMatchAnalysis(data) {
    const match = data?.match_assessment || {};
    const score = parseFloat(match.overall_match_score || 0);
    
    return `
        <div class="tab-section active">
            <div class="tab-header">
                <h2>Match Analysis</h2>
            </div>
            <div class="score-card">
                <div class="score-value">${score.toFixed(1)} / 5.0</div>
                <div class="score-label">Overall Match Score</div>
            </div>
            ${match.strengths ? `
                <div class="info-card">
                    <h3>Strengths</h3>
                    ${match.strengths.map(s => `<p>• ${s}</p>`).join('')}
                </div>
            ` : ''}
            ${match.gaps ? `
                <div class="info-card">
                    <h3>Gaps & Improvement Areas</h3>
                    ${match.gaps.map(g => `<p>• ${g}</p>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// Render Candidate Profile
function renderCandidateProfile(data) {
    const profile = data?.ideal_candidate_profile || {};
    
    return `
        <div class="tab-section active">
            <div class="tab-header">
                <h2>Ideal Candidate Profile</h2>
            </div>
            ${profile.required_experience ? `
                <div class="info-card">
                    <h3>Required Experience</h3>
                    <p>${profile.required_experience}</p>
                </div>
            ` : ''}
            ${profile.required_skills ? `
                <div class="info-card">
                    <h3>Required Skills</h3>
                    ${profile.required_skills.map(s => `<span class="tag">${s}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// Render Work Scenario
function renderWorkScenario(data) {
    const analysis = data?.job_role_team_analysis || {};
    
    return `
        <div class="tab-section active">
            <div class="tab-header">
                <h2>Work Scenario Analysis</h2>
            </div>
            ${analysis.daily_activities ? `
                <div class="info-card">
                    <h3>Daily Activities</h3>
                    ${analysis.daily_activities.map(a => `<p>• ${a}</p>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// Render Projects
function renderProjects(data) {
    const projects = data?.selected_projects || [];
    
    return `
        <div class="tab-section active">
            <div class="tab-header">
                <h2>Optimized Projects</h2>
            </div>
            ${projects.map((p, i) => `
                <div class="info-card">
                    <h3>${p.project_name || `Project ${i + 1}`}</h3>
                    <p>${p.relevance_reason || ''}</p>
                    ${p.optimized_version?.summary_bullets ? `
                        <h4>Optimized Summary:</h4>
                        ${p.optimized_version.summary_bullets.map(b => `<p>• ${b}</p>`).join('')}
                    ` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

// Render Resume Optimization
function renderResumeOptimization(data) {
    const replacements = data?.experience_replacements || [];
    const optimizations = data?.experience_optimizations || [];
    
    return `
        <div class="tab-section active">
            <div class="tab-header">
                <h2>Resume Optimization Recommendations</h2>
            </div>
            ${replacements.length > 0 ? `
                <div class="info-card">
                    <h3>Experience Replacements (${replacements.length})</h3>
                    ${replacements.map((r, i) => `
                        <div style="margin-bottom: 1rem;">
                            <p><strong>Replace:</strong> ${r.experience_to_replace?.title || 'N/A'}</p>
                            <p><strong>Reason:</strong> ${r.replacement_rationale?.why_replace || ''}</p>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            ${optimizations.length > 0 ? `
                <div class="info-card">
                    <h3>Experience Optimizations (${optimizations.length})</h3>
                    ${optimizations.map((o, i) => `
                        <div style="margin-bottom: 1rem;">
                            <p><strong>${o.experience_entry?.title || 'Experience'}</strong></p>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// Initialize App
function init() {
    setupCharCounters();
    setupPDFUpload();
    
    const form = document.getElementById('input-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    const retryBtn = document.getElementById('retry-btn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            if (state.retryCount >= 3) {
                alert('Maximum retry attempts reached. Please start over.');
                showPage('input');
                return;
            }
            state.retryCount++;
            // Reset and restart
            location.reload();
        });
    }

    const generateBtn = document.getElementById('generate-resume-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            try {
                const response = await fetch(`${API_BASE}/api/v1/resume/generate`, {
                    method: 'POST'
                });
                const data = await response.json();
                if (data.status === 'success') {
                    alert('Resume generated successfully!');
                    // Start interview preparation
                    if (state.workflowId) {
                        const interviewResponse = await fetch(`${API_BASE}/api/v1/interview/prepare`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ workflow_id: state.workflowId })
                        });
                        alert('Interview preparation started!');
                    }
                }
            } catch (error) {
                alert('Error generating resume: ' + error.message);
            }
        });
    }
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
