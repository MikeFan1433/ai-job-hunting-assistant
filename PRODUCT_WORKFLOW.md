# AI Job Hunting Assistant - Product Workflow & Architecture

> **Last Updated**: January 20, 2026  
> **Version**: 1.0.0  
> **Status**: Backend Complete (Frontend Pending)

---

## 📋 Table of Contents

1. [Product Overview](#product-overview)
2. [Complete Workflow](#complete-workflow)
3. [Agent Details](#agent-details)
4. [Key Inputs & Outputs](#key-inputs--outputs)
5. [Product Architecture](#product-architecture)
6. [API Endpoints](#api-endpoints)
7. [Data Flow](#data-flow)

---

## 🎯 Product Overview

**AI Job Hunting Assistant** is an end-to-end system that helps job seekers optimize their resumes, prepare for interviews, and maximize their chances of landing their dream job. The system uses a multi-agent workflow to provide comprehensive job application support.

### Core Value Proposition

- **Automated Resume Optimization**: AI-powered resume tailoring for each job application
- **Intelligent Project Packaging**: Transform project materials into compelling resume experiences
- **Comprehensive Interview Preparation**: Generate personalized interview questions and answers
- **Match Assessment**: Quantify your fit for each role with detailed analysis

### Target Users

- Job seekers with existing work experience
- Professionals applying to multiple positions
- Candidates who want to optimize their application materials
- Users who need interview preparation support

---

## 🔄 Complete Workflow

### High-Level Flow

```
User Input → Agent 1 (Validation) → Agent 2 (Analysis) → Agent 3 (Packaging) 
→ Agent 4 (Optimization) → User Feedback → Agent 5 (Interview Prep) → Final Outputs
```

### Detailed Step-by-Step Process

#### **Step 1: Input Collection & Validation**

**Trigger**: User submits resume, JD, and optional project materials

**Agent 1: Input Validation Agent**
- Validates resume completeness (work experience, education)
- Validates project materials (if provided)
- Supports both English and Chinese resumes
- Returns pass/fail with detailed feedback

**Output**: Validation result with specific issues (if any)

**User Action**: Fix any validation issues before proceeding

---

#### **Step 2: JD Analysis & Matching Assessment**

**Trigger**: Validation passes

**Agent 2: JD Analysis & Matching Assessment Agent**
- Deep analysis of JD requirements
- Creates ideal candidate profile
- Analyzes candidate's current profile
- Calculates match score (0-5 scale)
- Provides ROI-based improvement recommendations

**Key Outputs**:
- `job_role_team_analysis`: Work scenarios, daily activities, project types
- `ideal_candidate_profile`: Required experience, skills, project portfolio
- `match_assessment`: Match score, strengths, gaps
- `improvement_recommendations`: Prioritized action items

---

#### **Step 3: Project Packaging & Optimization**

**Trigger**: Agent 2 analysis complete

**Agent 3: Project Packaging Agent**
- Selects most relevant projects (up to 5)
- Restructures projects using 5-part framework:
  1. Goals (What & Why)
  2. Methods & Solution (How)
  3. Execution & Timeline (Process)
  4. Results & Metrics (Outcome)
  5. Learning & Reflection
- Identifies gaps and enriches content
- Optimizes for JD alignment

**Key Outputs**:
- `selected_projects`: Optimized project texts with full framework
- `skipped_projects`: Projects not selected with reasons

---

#### **Step 4: Resume Optimization**

**Trigger**: Agent 3 packaging complete

**Agent 4: Resume Optimization Agent**

**4.1 Experience Replacement Analysis**
- Analyzes each resume experience
- Selects least relevant experiences (matching number of optimized projects)
- Generates replacement recommendations
- Classifies projects (resume_adopted vs. resume_not_adopted)

**4.2 Format & Content Adjustment**
- Provides adjustment suggestions for each experience
- Keyword optimization
- Expression refinement
- Metric addition

**User Feedback Loop**:
- User reviews recommendations
- User submits feedback (accept/reject/modify) for each suggestion
- System applies accepted changes

**Key Outputs**:
- `experience_replacements`: Replacement recommendations
- `format_content_adjustments`: Content improvement suggestions
- `project_classification`: Projects categorized for interview prep

**After User Feedback**:
- `final_resume`: Optimized resume with all accepted changes
- `classified_projects`: Projects organized for interview preparation

---

#### **Step 5: Interview Preparation**

**Trigger**: User confirms resume modifications

**Agent 5: Interview Preparation Agent**

**5.1 Behavioral Interview Questions**
- Self-introduction (3-paragraph template)
- Storytelling example (Hook → Emergency → Action → Impact → Reflection)
- Top 10 behavioral questions with TREAT principle answers

**5.2 Project Deep-Dive Questions**
- Selects top 3 projects (from resume_adopted_projects or resume experiences)
- STAR format overview for each project
- 5 technical detail questions per project (with answer guidance)

**5.3 Business Domain Questions**
- 10 business-related questions based on role analysis
- Each with "why they ask" and "how to answer" guidance

**Key Outputs**:
- `theme_1_behavioral_interview`: Self-intro, storytelling, behavioral Q&A
- `theme_2_project_deep_dive`: Top 3 projects with technical questions
- `theme_3_business_domain`: Business questions and answers

---

## 🤖 Agent Details

### Agent 1: Input Validation Agent

**Purpose**: Validate input completeness before processing

**Model**: `gpt-4o-mini` (cost-efficient)

**Inputs**:
- Resume text (required)
- Project materials (optional)

**Outputs**:
```json
{
  "is_valid": true/false,
  "has_work_experience": true/false,
  "work_experience_count": 0,
  "work_experience_issues": [],
  "has_education": true/false,
  "education_count": 0,
  "education_issues": [],
  "has_project_materials": true/false,
  "project_materials_provided": true/false,
  "project_count": 0,
  "project_issues": [],
  "missing_sections": [],
  "validation_summary": "...",
  "recommendations": []
}
```

**Key Features**:
- Bilingual support (English & Chinese)
- Project materials validation (optional)
- Clear pass/fail with detailed feedback

---

### Agent 2: JD Analysis & Matching Assessment Agent

**Purpose**: Comprehensive JD analysis and candidate matching

**Model**: `supermind-agent-v1` (complex analysis)

**Inputs**:
- JD text
- Resume text
- Project materials (optional)

**Outputs**:
```json
{
  "job_role_team_analysis": {
    "team_objectives": "...",
    "work_scenarios": ["..."],
    "daily_activities": ["..."],
    "project_types": ["..."],
    "methods_technologies": ["..."],
    "collaboration_patterns": "...",
    "kpis": ["..."],
    "required_knowledge": ["..."]
  },
  "ideal_candidate_profile": {
    "overall_industry_experience": {...},
    "business_domain_understanding": {...},
    "project_portfolio_experience": {...},
    "hard_skills": {...},
    "soft_skills_top5": [...]
  },
  "candidate_profile": {
    "industry_experience": {...},
    "business_domain_understanding": {...},
    "project_portfolio": {...},
    "hard_skills": {...},
    "soft_skills": {...}
  },
  "match_assessment": {
    "overall_match_score": 0.0,
    "match_level": "Excellent/Strong/Moderate/Weak/Poor",
    "industry_match": {...},
    "experience_match": {...},
    "skills_match": {...},
    "overall_summary": "...",
    "application_prospects": "..."
  },
  "improvement_recommendations": [...]
}
```

**Key Features**:
- Industry-agnostic (works for ALL industries)
- Weighted scoring (30% Industry, 40% Experience, 30% Skills)
- ROI-based recommendations
- Detailed skill gaps analysis

---

### Agent 3: Project Packaging Agent

**Purpose**: Select and optimize projects for JD alignment

**Model**: `supermind-agent-v1` (complex analysis)

**Inputs**:
- JD text
- Project materials
- Agent 2 outputs

**Outputs**:
```json
{
  "selected_projects": [
    {
      "project_name": "...",
      "relevance_reason": "...",
      "gaps_identified": [...],
      "rewritten_with_gaps": {
        "goals": {...},
        "methods_solution": {...},
        "execution_timeline": {...},
        "results_metrics": {...},
        "learning_reflection": {...}
      },
      "optimized_version": {
        "summary_bullets": [...],
        "jd_keywords_highlighted": [...]
      }
    }
  ],
  "skipped_projects": [...]
}
```

**Key Features**:
- 5-part framework restructuring
- Gap identification and enrichment
- JD keyword alignment
- Maximum 5 projects selected

---

### Agent 4: Resume Optimization Agent

**Purpose**: Optimize resume through experience replacement and content adjustment

**Model**: `supermind-agent-v1` (complex analysis)

**Inputs**:
- JD text
- Resume text
- Agent 2 outputs
- Agent 3 outputs

**Outputs**:
```json
{
  "experience_replacements": [
    {
      "experience_to_replace": {...},
      "replacement_project": {...},
      "replacement_rationale": {...},
      "replacement_instructions": {
        "resume_experience_description": "...",
        "new_bullets": [...]
      }
    }
  ],
  "project_classification": {
    "resume_adopted_projects": [...],
    "resume_not_adopted_projects": [...]
  },
  "format_content_adjustments": [...]
}
```

**After User Feedback**:
```json
{
  "final_resume": "...",
  "classified_projects": {
    "resume_adopted_projects": [...],
    "resume_not_adopted_projects": [...]
  }
}
```

**Key Features**:
- Experience replacement recommendations
- Project classification for interview prep
- User feedback integration
- Final resume generation

---

### Agent 5: Interview Preparation Agent

**Purpose**: Generate comprehensive interview preparation materials

**Model**: `supermind-agent-v1` (complex analysis)

**Inputs**:
- JD text
- Final optimized resume
- Agent 2 outputs
- Agent 4 outputs (classified_projects)

**Outputs**:
```json
{
  "theme_1_behavioral_interview": {
    "self_introduction": {
      "paragraph_1": "...",
      "paragraph_2": "...",
      "paragraph_3": "...",
      "full_text": "..."
    },
    "storytelling_example": {
      "selected_project": {...},
      "hook": "...",
      "emergency": "...",
      "approach": "...",
      "action": "...",
      "impact": "...",
      "reflection": "...",
      "full_storytelling_answer": "..."
    },
    "top_10_behavioral_questions": [
      {
        "question": "...",
        "why_they_ask_this": "...",
        "sample_answer": "...",
        "treat_principles_applied": {...}
      }
    ]
  },
  "theme_2_project_deep_dive": {
    "selected_projects": [
      {
        "project_overview_star": {
          "situation": "...",
          "task": "...",
          "action": "...",
          "result": "..."
        },
        "technical_deep_dive_questions": [
          {
            "question": "...",
            "why_they_ask_this": "...",
            "how_to_answer": {...}
          }
        ]
      }
    ]
  },
  "theme_3_business_domain": {
    "business_questions": [
      {
        "question": "...",
        "why_they_ask_this": "...",
        "how_to_answer": {...}
      }
    ]
  }
}
```

**Key Features**:
- Introduction template integration
- Storytelling template (Hook → Emergency → Action → Impact → Reflection)
- TREAT principle for behavioral questions
- STAR format for project overviews
- Top 3 projects with technical deep-dive

---

## 📥📤 Key Inputs & Outputs

### Step 1: Input Validation

**Inputs**:
- `resume_text`: String (required)
- `project_materials`: String (optional)

**Outputs**:
- `is_valid`: Boolean
- `validation_summary`: String
- `recommendations`: Array of strings

---

### Step 2: JD Analysis

**Inputs**:
- `jd_text`: String
- `resume_text`: String
- `project_materials`: String (optional)

**Outputs**:
- `job_role_team_analysis`: Object
- `ideal_candidate_profile`: Object
- `candidate_profile`: Object
- `match_assessment`: Object (with `overall_match_score`: 0-5)
- `improvement_recommendations`: Array

---

### Step 3: Project Packaging

**Inputs**:
- `jd_text`: String
- `project_materials`: String
- `agent2_outputs`: Object (from Step 2)

**Outputs**:
- `selected_projects`: Array (max 5 projects)
- `skipped_projects`: Array

---

### Step 4: Resume Optimization

**Inputs**:
- `jd_text`: String
- `resume_text`: String
- `agent2_outputs`: Object
- `agent3_outputs`: Object

**Outputs (Initial)**:
- `experience_replacements`: Array
- `format_content_adjustments`: Array
- `project_classification`: Object

**User Feedback**:
- User reviews and submits feedback for each recommendation

**Outputs (After Feedback)**:
- `final_resume`: String
- `classified_projects`: Object
  - `resume_adopted_projects`: Array
  - `resume_not_adopted_projects`: Array

---

### Step 5: Interview Preparation

**Inputs**:
- `jd_text`: String
- `final_resume`: String (from Step 4)
- `agent2_outputs`: Object
- `agent4_outputs`: Object (with `classified_projects`)

**Outputs**:
- `theme_1_behavioral_interview`: Object
  - `self_introduction`: Object
  - `storytelling_example`: Object
  - `top_10_behavioral_questions`: Array
- `theme_2_project_deep_dive`: Object
  - `selected_projects`: Array (top 3)
- `theme_3_business_domain`: Object
  - `business_questions`: Array (10 questions)

---

## 🏗️ Product Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                  User Interface (Frontend)              │
│                    (To be implemented)                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (resume_optimization_api)  │
│  - POST /api/v1/resume/optimize                         │
│  - POST /api/v1/resume/feedback                         │
│  - POST /api/v1/resume/generate                         │
│  - POST /api/v1/resume/export                           │
│  - GET  /api/v1/projects/classified                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    Agent Workflow                       │
│                                                          │
│  Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5        │
│  (Validation) (Analysis) (Packaging) (Optimization)    │
│                                                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Student Portal API (LLM Service)           │
│  - /v1/chat/completions                                 │
│  - /v1/embeddings                                        │
│  - /v1/search                                            │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input
    │
    ├─→ Agent 1: Validation
    │       │
    │       └─→ Pass/Fail
    │
    ├─→ Agent 2: JD Analysis
    │       │
    │       ├─→ job_role_team_analysis
    │       ├─→ ideal_candidate_profile
    │       ├─→ match_assessment
    │       └─→ improvement_recommendations
    │
    ├─→ Agent 3: Project Packaging
    │       │
    │       └─→ selected_projects (optimized)
    │
    ├─→ Agent 4: Resume Optimization
    │       │
    │       ├─→ experience_replacements
    │       ├─→ format_content_adjustments
    │       └─→ project_classification
    │
    │       [User Feedback Loop]
    │
    │       ├─→ final_resume
    │       └─→ classified_projects
    │
    └─→ Agent 5: Interview Preparation
            │
            ├─→ theme_1_behavioral_interview
            ├─→ theme_2_project_deep_dive
            └─→ theme_3_business_domain
```

---

## 🔌 API Endpoints

### Resume Optimization API

**Base URL**: `/api/v1/resume`

#### 1. Optimize Resume
- **Endpoint**: `POST /api/v1/resume/optimize`
- **Request**:
```json
{
  "jd_text": "...",
  "resume_text": "...",
  "agent2_outputs": {...},
  "agent3_outputs": {...}
}
```
- **Response**: Optimization recommendations

#### 2. Submit Feedback
- **Endpoint**: `POST /api/v1/resume/feedback`
- **Request**:
```json
{
  "feedback_type": "experience_replacement" | "format_adjustment",
  "item_id": "...",
  "feedback": "accept" | "reject" | "further_modify",
  "additional_notes": "..."
}
```

#### 3. Generate Final Resume
- **Endpoint**: `POST /api/v1/resume/generate`
- **Response**:
```json
{
  "final_resume": "...",
  "classified_projects": {...},
  "modifications_applied": [...]
}
```

#### 4. Export Resume
- **Endpoint**: `POST /api/v1/resume/export`
- **Request**:
```json
{
  "format": "pdf" | "docx",
  "title": "..."
}
```

#### 5. Get Classified Projects
- **Endpoint**: `GET /api/v1/projects/classified`
- **Response**: Projects organized for interview preparation

---

## 📊 Product Metrics & Success Criteria

### Key Performance Indicators

1. **Match Score Improvement**: Average increase in match score after optimization
2. **User Satisfaction**: Feedback on recommendation quality
3. **Time Saved**: Reduction in manual resume tailoring time
4. **Interview Success Rate**: Improvement in interview performance

### Success Criteria

- ✅ All 5 agents functional and tested
- ✅ End-to-end workflow operational
- ✅ User feedback system working
- ✅ Resume export functional (PDF/DOCX)
- ⏳ Frontend UI (pending)

---

## 🚀 Deployment Status

### Completed ✅
- Agent 1: Input Validation
- Agent 2: JD Analysis & Matching
- Agent 3: Project Packaging
- Agent 4: Resume Optimization
- Agent 5: Interview Preparation
- Resume Optimization Service
- Resume Export (PDF/DOCX)
- API Endpoints
- User Feedback System

### Pending ⏳
- Frontend UI/Interface
- User Authentication
- Data Persistence
- Real-time Progress Updates

---

## 📝 Notes

- All agents use the Student Portal API for LLM services
- Agent 1 uses cost-efficient model (`gpt-4o-mini`)
- Agents 2-5 use complex analysis model (`supermind-agent-v1`)
- All outputs are in JSON format for easy integration
- System supports both English and Chinese resumes
- Project materials are optional but enhance optimization quality

---

**End of Document**
