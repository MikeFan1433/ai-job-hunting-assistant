"""Complete Workflow API - All Agents Endpoints."""
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Optional, List
import json
import asyncio
from datetime import datetime
import os
from pdf_parser import extract_text_from_pdf, validate_pdf

# Import all agents
from agent1 import InputValidationAgent
from agent2 import JDAnalysisAgent
from agent3 import ProjectPackagingAgent
from agent4 import ResumeOptimizationAgent
from agent5 import InterviewPreparationAgent

# Import services
from resume_optimization_service import ResumeOptimizationService
from resume_export import ResumeExporter

app = FastAPI(title="AI Job Hunting Assistant API", version="1.0.0")

# CORS middleware for frontend
# Allow all origins for sharing (in production, restrict this to specific domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for easy sharing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
agent1 = InputValidationAgent()
agent2 = JDAnalysisAgent()
agent3 = ProjectPackagingAgent()
agent4 = ResumeOptimizationAgent()
agent5 = InterviewPreparationAgent()
optimization_service = ResumeOptimizationService()
exporter = ResumeExporter()

# Global state for workflow execution
workflow_state = {}

# Store workflow results for later use (Agent 5 needs Agent 2 outputs)
workflow_results = {}


# ============================================================================
# Request Models
# ============================================================================

class WorkflowStartRequest(BaseModel):
    """Request to start the complete workflow."""
    jd_text: str
    resume_text: str
    projects_text: Optional[str] = None


@app.post("/api/v1/upload/resume-pdf")
async def upload_resume_pdf(file: UploadFile = File(...)) -> Dict:
    """
    Upload and parse PDF resume.
    
    Returns:
        Dictionary with extracted text and validation status
    """
    try:
        # Read file content
        pdf_content = await file.read()
        
        # Validate PDF
        is_valid, error_msg = validate_pdf(pdf_content)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg or "Invalid PDF file")
        
        # Extract text
        extracted_text = extract_text_from_pdf(pdf_content)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="PDF appears to be empty or unreadable")
        
        return {
            "status": "success",
            "extracted_text": extracted_text,
            "file_name": file.filename,
            "file_size": len(pdf_content),
            "text_length": len(extracted_text)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    feedback_type: str  # "experience_replacement", "format_adjustment", "experience_optimization", or "skills_optimization"
    item_id: str
    feedback: str  # "accept", "further_modify", or "reject"
    additional_notes: Optional[str] = None
    modified_text: Optional[str] = None  # For "further_modify" with inline edits


class ExportRequest(BaseModel):
    """Request model for resume export."""
    format: str = "pdf"  # "pdf" or "docx"
    title: str = "Resume"


# ============================================================================
# Workflow Execution Endpoints
# ============================================================================

@app.post("/api/v1/workflow/start")
async def start_workflow(request: WorkflowStartRequest, background_tasks: BackgroundTasks) -> Dict:
    """
    Start the complete workflow: Agent 1 → 2 → 3 → 4.
    Returns workflow ID for progress tracking immediately.
    Executes in background - use progress endpoint to track.
    
    This endpoint is designed to return immediately to avoid gateway timeouts.
    """
    import asyncio
    
    # Generate workflow ID
    workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize workflow state immediately (synchronous, fast operation)
    workflow_state[workflow_id] = {
        "status": "running",
        "current_step": "agent1",
        "progress": 0,
        "message": "Starting workflow...",
        "results": {},
        "error": None
    }
    
    # Schedule background execution using asyncio.create_task for true async
    # This ensures the endpoint returns immediately without waiting
    async def schedule_workflow():
        # Small delay to ensure response is sent first
        await asyncio.sleep(0.1)
        await execute_workflow_async(
            workflow_id,
            request.jd_text,
            request.resume_text,
            request.projects_text
        )
    
    # Use asyncio.create_task for true async execution
    # This is faster than BackgroundTasks for immediate return
    asyncio.create_task(schedule_workflow())
    
    # Return immediately - don't wait for any initialization
    return {
        "status": "started",
        "workflow_id": workflow_id,
        "message": "Workflow started. Use /api/v1/workflow/progress/{workflow_id} to track progress."
    }


@app.get("/api/v1/workflow/progress/{workflow_id}")
async def get_workflow_progress(workflow_id: str) -> Dict:
    """Get current workflow progress."""
    if workflow_id not in workflow_state:
        # Return a pending state instead of 404 to handle initialization delay
        # This prevents frontend from showing errors during workflow startup
        return {
            "status": "running",
            "current_step": "agent1",
            "progress": 0,
            "message": "Workflow is initializing...",
            "results": {},
            "error": None
        }
    
    return workflow_state[workflow_id]


@app.get("/api/v1/workflow/progress/{workflow_id}/stream")
async def stream_workflow_progress(workflow_id: str):
    """
    Stream workflow progress using Server-Sent Events (SSE).
    """
    async def event_generator():
        # Wait for workflow to be created (max 10 seconds)
        max_wait = 10
        waited = 0
        while workflow_id not in workflow_state and waited < max_wait:
            await asyncio.sleep(0.5)
            waited += 0.5
        
        # If still not found, send initializing state
        if workflow_id not in workflow_state:
            initializing_state = {
                "status": "running",
                "current_step": "agent1",
                "progress": 0,
                "message": "Workflow is initializing...",
                "results": {},
                "error": None
            }
            yield f"data: {json.dumps(initializing_state)}\n\n"
            # Wait a bit more for workflow to start
            await asyncio.sleep(2)
        
        # Now stream actual progress
        while workflow_id in workflow_state:
            state = workflow_state[workflow_id]
            
            # Send current progress
            yield f"data: {json.dumps(state)}\n\n"
            
            # If completed or failed, break
            if state["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)  # Update every second
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def execute_workflow_async(workflow_id: str, jd_text: str, resume_text: str, projects_text: Optional[str]):
    """Execute workflow in background."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if workflow_id not in workflow_state:
            logger.error(f"Workflow {workflow_id} not found in state")
            return
        
        state = workflow_state[workflow_id]
        logger.info(f"Starting workflow execution for {workflow_id}")
        
        # Agent 1: Input Validation
        state["current_step"] = "agent1"
        state["progress"] = 10
        state["message"] = "Validating inputs..."
        logger.info(f"Agent 1: Starting validation")
        try:
            agent1_result = agent1.validate_inputs(
                resume_text=resume_text,
                project_materials=projects_text
            )
            state["results"]["agent1"] = agent1_result
            
            if not agent1_result.get("is_valid", False) and "error" not in agent1_result:
                # Check if there are critical issues
                issues = agent1_result.get("issues", [])
                critical_issues = [i for i in issues if i.get("severity") == "critical"]
                if critical_issues:
                    state["status"] = "failed"
                    state["error"] = "Input validation failed with critical issues"
                    return
        except Exception as e:
            import traceback
            error_msg = f"Agent 1 error: {str(e)}"
            logger.error(f"Agent 1 failed: {error_msg}\n{traceback.format_exc()}")
            state["status"] = "failed"
            state["error"] = error_msg
            return
        
        # Agent 2: JD Analysis
        state["current_step"] = "agent2"
        state["progress"] = 30
        state["message"] = "Analyzing JD and generating candidate profile..."
        try:
            agent2_result = agent2.analyze_jd_and_match(
                jd_text=jd_text,
                resume_text=resume_text,
                project_materials=projects_text
            )
            state["results"]["agent2"] = agent2_result
        except Exception as e:
            state["status"] = "failed"
            state["error"] = f"Agent 2 error: {str(e)}"
            return
        
        # Agent 3: Project Packaging
        state["current_step"] = "agent3"
        state["progress"] = 50
        state["message"] = "Packaging and optimizing projects..."
        try:
            agent3_result = agent3.package_projects(
                jd_text=jd_text,
                project_materials=projects_text or "",
                agent2_outputs=agent2_result
            )
            state["results"]["agent3"] = agent3_result
        except Exception as e:
            state["status"] = "failed"
            state["error"] = f"Agent 3 error: {str(e)}"
            return
        
        # Agent 4: Resume Optimization
        state["current_step"] = "agent4"
        state["progress"] = 70
        state["message"] = "Generating resume optimization recommendations..."
        try:
            # Load data into service
            optimization_service.load_original_resume(resume_text)
            optimization_service.load_agent3_outputs(agent3_result)
            
            agent4_result = agent4.optimize_resume(
                jd_text=jd_text,
                resume_text=resume_text,
                agent2_outputs=agent2_result,
                agent3_outputs=agent3_result
            )
            
            optimization_service.load_optimization_recommendations(agent4_result)
            state["results"]["agent4"] = agent4_result
        except Exception as e:
            state["status"] = "failed"
            state["error"] = f"Agent 4 error: {str(e)}"
            return
        
        # Store results for later use (Agent 5)
        workflow_results[workflow_id] = {
            "jd_text": jd_text,
            "resume_text": resume_text,
            "agent2_outputs": agent2_result,
            "agent3_outputs": agent3_result,
            "agent4_outputs": agent4_result
        }
        
        # Complete
        state["current_step"] = "completed"
        state["progress"] = 100
        state["status"] = "completed"
        state["message"] = "Workflow completed successfully!"
        
    except Exception as e:
        import traceback
        error_msg = f"Workflow error: {str(e)}"
        logger.error(f"Workflow execution failed: {error_msg}\n{traceback.format_exc()}")
        if workflow_id in workflow_state:
            workflow_state[workflow_id]["status"] = "failed"
            workflow_state[workflow_id]["error"] = error_msg


@app.get("/api/v1/workflow/result/{workflow_id}")
async def get_workflow_result(workflow_id: str) -> Dict:
    """Get workflow results after completion."""
    if workflow_id not in workflow_state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    state = workflow_state[workflow_id]
    if state["status"] != "completed":
        raise HTTPException(status_code=400, detail="Workflow not completed yet")
    
    return {
        "status": "success",
        "workflow_id": workflow_id,
        "results": state["results"]
    }


# ============================================================================
# Resume Optimization Endpoints (Agent 4)
# ============================================================================

@app.post("/api/v1/resume/feedback")
async def submit_feedback(request: FeedbackRequest) -> Dict:
    """Submit user feedback for optimization recommendations."""
    try:
        result = optimization_service.submit_feedback(
            feedback_type=request.feedback_type,
            item_id=request.item_id,
            feedback=request.feedback,
            additional_notes=request.additional_notes
        )
        
        # If "further_modify" with modified_text, apply the modification
        if request.feedback == "further_modify" and request.modified_text:
            # Store the modified text for later application
            result["modified_text"] = request.modified_text
        
        return {
            "status": "success",
            "feedback_result": result,
            "feedback_status": optimization_service.get_feedback_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@app.post("/api/v1/resume/feedback/batch")
async def submit_batch_feedback(feedbacks: List[FeedbackRequest]) -> Dict:
    """Submit multiple feedbacks at once (for "accept all")."""
    try:
        results = []
        for feedback in feedbacks:
            result = optimization_service.submit_feedback(
                feedback_type=feedback.feedback_type,
                item_id=feedback.item_id,
                feedback=feedback.feedback,
                additional_notes=feedback.additional_notes
            )
            results.append(result)
        
        return {
            "status": "success",
            "results": results,
            "feedback_status": optimization_service.get_feedback_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting batch feedback: {str(e)}")


@app.get("/api/v1/resume/feedback/status")
async def get_feedback_status() -> Dict:
    """Get current feedback status."""
    try:
        return {
            "status": "success",
            "feedback_status": optimization_service.get_feedback_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting feedback status: {str(e)}")


@app.post("/api/v1/resume/generate")
async def generate_final_resume() -> Dict:
    """Generate final optimized resume after all feedback."""
    try:
        result = optimization_service.apply_feedback_and_generate_resume()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "final_resume": result["final_resume"],
            "classified_projects": result.get("classified_projects", {}),
            "modifications_applied": result["modifications_applied"],
            "summary": result["summary"],
            "project_classification": result.get("project_classification", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating final resume: {str(e)}")


@app.get("/api/v1/resume/recommendations")
async def get_recommendations() -> Dict:
    """Get current optimization recommendations."""
    try:
        if not optimization_service.optimization_recommendations:
            raise HTTPException(status_code=404, detail="No recommendations available")
        
        return {
            "status": "success",
            "recommendations": optimization_service.optimization_recommendations,
            "user_feedback": optimization_service.user_feedback,
            "project_classification": optimization_service.get_project_classification()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


# ============================================================================
# Interview Preparation Endpoints (Agent 5)
# ============================================================================

class InterviewPrepareRequest(BaseModel):
    """Request to start interview preparation."""
    workflow_id: str


@app.post("/api/v1/interview/prepare")
async def prepare_interview(request: InterviewPrepareRequest, background_tasks: BackgroundTasks) -> Dict:
    """
    Start Agent 5 interview preparation.
    Requires workflow_id to get Agent 2 outputs.
    """
    if not optimization_service.final_resume:
        raise HTTPException(status_code=400, detail="Final resume not available. Please generate it first.")
    
    if request.workflow_id not in workflow_results:
        raise HTTPException(status_code=404, detail="Workflow results not found. Please complete workflow first.")
    
    interview_id = f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    workflow_state[interview_id] = {
        "status": "running",
        "progress": 0,
        "message": "Preparing interview materials...",
        "result": None,
        "error": None
    }
    
    # Get required data
    final_resume = optimization_service.final_resume
    classified_projects = optimization_service.get_classified_projects_for_interview()
    workflow_data = workflow_results[request.workflow_id]
    
    background_tasks.add_task(
        execute_interview_prep_async,
        interview_id,
        workflow_data["jd_text"],
        final_resume,
        workflow_data["agent2_outputs"],
        classified_projects
    )
    
    return {
        "status": "started",
        "interview_id": interview_id,
        "message": "Interview preparation started"
    }


async def execute_interview_prep_async(
    interview_id: str,
    jd_text: str,
    final_resume: str,
    agent2_outputs: Dict,
    classified_projects: Dict
):
    """Execute Agent 5 in background."""
    try:
        state = workflow_state[interview_id]
        
        state["progress"] = 30
        state["message"] = "Generating behavioral interview questions..."
        
        agent4_outputs = {
            "classified_projects": classified_projects
        }
        
        # Execute Agent 5
        agent5_result = agent5.prepare_interview(
            jd_text=jd_text,
            final_resume=final_resume,
            agent2_outputs=agent2_outputs,
            agent4_outputs=agent4_outputs
        )
        
        state["progress"] = 100
        state["status"] = "completed"
        state["result"] = agent5_result
        state["message"] = "Interview preparation completed!"
        
    except Exception as e:
        state["status"] = "failed"
        state["error"] = f"Interview preparation error: {str(e)}"


@app.get("/api/v1/interview/progress/{interview_id}")
async def get_interview_progress(interview_id: str) -> Dict:
    """Get interview preparation progress."""
    if interview_id not in workflow_state:
        raise HTTPException(status_code=404, detail="Interview preparation not found")
    
    return workflow_state[interview_id]


@app.get("/api/v1/interview/result/{interview_id}")
async def get_interview_result(interview_id: str) -> Dict:
    """Get interview preparation result."""
    if interview_id not in workflow_state:
        raise HTTPException(status_code=404, detail="Interview preparation not found")
    
    state = workflow_state[interview_id]
    if state["status"] != "completed":
        raise HTTPException(status_code=400, detail="Interview preparation not completed yet")
    
    return {
        "status": "success",
        "result": state["result"]
    }


# ============================================================================
# Export Endpoints
# ============================================================================

@app.post("/api/v1/resume/export")
async def export_resume(request: ExportRequest) -> Dict:
    """Export final resume to PDF or DOCX."""
    try:
        if not optimization_service.final_resume:
            raise HTTPException(status_code=400, detail="Final resume not available")
        
        output_path = f"data/resumes/final_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}"
        result = exporter.export(
            resume_text=optimization_service.final_resume,
            output_path=output_path,
            format=request.format,
            title=request.title
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "status": "success",
            "export_result": result,
            "download_url": f"/api/v1/resume/download/{request.format}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting resume: {str(e)}")


# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/api/v1/projects/classified")
async def get_classified_projects() -> Dict:
    """Get classified projects for interview preparation."""
    try:
        classified_projects = optimization_service.get_classified_projects_for_interview()
        return {
            "status": "success",
            "classified_projects": classified_projects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting classified projects: {str(e)}")


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    """Root endpoint - serve the main HTML page."""
    # Try frontend dist first
    index_file = os.path.join(frontend_dist_dir, "index.html")
    if os.path.exists(index_file):
        from fastapi.responses import FileResponse
        return FileResponse(index_file)
    
    # Fallback to static directory
    static_file = os.path.join(static_dir, "index.html")
    if os.path.exists(static_file):
        from fastapi.responses import FileResponse
        return FileResponse(static_file)
    
    return {
        "name": "AI Job Hunting Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "workflow": "/api/v1/workflow/start",
            "resume": "/api/v1/resume/*",
            "interview": "/api/v1/interview/prepare"
        }
    }


# Mount static files (HTML, CSS, JS) - MUST be after all API routes
static_dir = os.path.join(os.path.dirname(__file__), "static")
frontend_dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# Serve frontend build files if they exist (production)
if os.path.exists(frontend_dist_dir):
    # Serve static assets
    assets_dir = os.path.join(frontend_dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # Serve frontend index.html for all non-API routes
    # IMPORTANT: This must be the LAST route registered to avoid conflicts with API routes
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend app for all non-API routes."""
        # Don't serve frontend for API routes (should not reach here if API routes are registered first)
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Don't serve frontend for asset routes (already handled by mount)
        if full_path.startswith("assets/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        index_file = os.path.join(frontend_dist_dir, "index.html")
        if os.path.exists(index_file):
            from fastapi.responses import FileResponse
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend not found")
elif os.path.exists(static_dir):
    # Fallback to old static directory
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
