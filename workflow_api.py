"""Complete Workflow API - All Agents Endpoints."""
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Optional, List
import json
import asyncio
from datetime import datetime
import io
import os
import logging
import re
from pdf_parser import extract_text_from_pdf, validate_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import all agents
from agent1 import InputValidationAgent
from agent2 import JDAnalysisAgent
from agent3 import ProjectPackagingAgent
from agent4 import ResumeOptimizationAgent
from agent5 import InterviewPreparationAgent

# Import services
from resume_optimization_service import ResumeOptimizationService
from resume_export import ResumeExporter
from config import AGENT2_FAST_MODE, AI_BUILDER_BASE_URL, STUDENT_PORTAL_API_KEY, LLM_MODEL_JSON, AGENT5_DISABLED
from workflow_ui_messages import workflow_progress_message
import httpx

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
    job_title: str  # Required
    company_name: str  # Required
    country_or_region: Optional[str] = None  # Optional
    jd_text: str
    resume_text: str
    projects_text: Optional[str] = None  # Optional, max 1000 chars recommended
    preferred_lang: Optional[str] = "en"  # "en" | "zh" for output language


class Agent2QuickRequest(BaseModel):
    """Request for quick Agent2-only JD analysis."""
    job_title: str
    company_name: str
    country_or_region: Optional[str] = None
    jd_text: str
    resume_text: str
    projects_text: Optional[str] = None
    preferred_lang: Optional[str] = "en"


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


@app.post("/api/v1/agent2/quick-analyze")
async def agent2_quick_analyze(request: Agent2QuickRequest) -> Dict:
    """
    Run Agent 2 (JD analysis & match) only and return results directly.
    Intended for low-latency MVP experiences.
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"🚀 Agent2 quick analyze requested (job_title={request.job_title}, company={request.company_name})"
    )
    try:
        result = agent2.analyze_jd_and_match(
            jd_text=request.jd_text,
            resume_text=request.resume_text,
            project_materials=request.projects_text,
            fast_mode=True,
            parallel_20s=True,
            job_title=request.job_title or None,
            company_name=request.company_name or None,
            country_or_region=request.country_or_region,
            preferred_lang=request.preferred_lang or "en",
        )
        return {
            "status": "success",
            "agent2": result,
        }
    except Exception as e:
        logger.exception("Agent 2 quick analyze failed")
        raise HTTPException(status_code=500, detail=f"Agent 2 quick analyze failed: {str(e)}")


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    feedback_type: str  # "experience_replacement", "format_adjustment", "experience_optimization", or "skills_optimization"
    item_id: str
    feedback: str  # "accept", "further_modify", or "reject"
    additional_notes: Optional[str] = None
    modified_text: Optional[str] = None  # For "further_modify" with inline edits


class RegenerateSuggestionRequest(BaseModel):
    """Request to regenerate a single suggestion using natural language instruction."""
    workflow_id: str
    feedback_type: str  # Only "format_adjustment" supported for now
    item_id: str
    user_instruction: str  # Natural language, e.g. "make it more quantitative"


class ExportRequest(BaseModel):
    """Request model for resume export."""
    format: str = "pdf"  # "pdf" or "docx"
    title: str = "Resume"


class ExportTextDocumentRequest(BaseModel):
    """Export arbitrary plain text to PDF (e.g. full interview prep from client-built text)."""
    title: str = "Interview_Prep"
    text: str
    format: str = "pdf"


MAX_TEXT_DOCUMENT_EXPORT_CHARS = 600_000


def _regenerate_bullet_suggestion(original: str, suggested: str, user_instruction: str, jd_snippet: str) -> str:
    """Call LLM to produce a new suggested bullet from user instruction. Returns new text or raises."""
    prompt = f"""You are a resume editor. Rewrite the following resume bullet according to the user's instruction.
Keep it professional and aligned with the job description. Output ONLY the new bullet text, one line, no quotes or preamble.

Original bullet:
{original}

Current suggested bullet:
{suggested}

Job description (excerpt):
{jd_snippet[:800]}

User instruction: {user_instruction}

New bullet (output only this line):"""
    endpoint = f"{AI_BUILDER_BASE_URL.rstrip('/')}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {STUDENT_PORTAL_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": LLM_MODEL_JSON,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 300,
    }
    with httpx.Client(timeout=25.0) as client:
        r = client.post(endpoint, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
    return content or suggested


# ============================================================================
# Workflow Execution Endpoints
# ============================================================================

@app.post("/api/v1/workflow/start")
async def start_workflow(request: WorkflowStartRequest, background_tasks: BackgroundTasks) -> Dict:
    """
    Start the workflow by returning workflow_id immediately.
    Agent 1 (validation) and Agents 2→3→4 run asynchronously in the background,
    so the frontend can navigate to the loading/result page without request delay.
    """
    import logging
    import asyncio
    logger = logging.getLogger(__name__)

    logger.info(f"📥 Received workflow start request (job_title={request.job_title}, company={request.company_name})")
    logger.info(f"   JD length: {len(request.jd_text)}")
    logger.info(f"   Resume length: {len(request.resume_text)}")
    logger.info(f"   Projects length: {len(request.projects_text) if request.projects_text else 0}")

    # Generate workflow ID and initialize state first (so frontend can poll immediately)
    workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    _pl = request.preferred_lang or "en"
    workflow_state[workflow_id] = {
        "status": "running",
        "current_step": "agent1",
        "progress": 0,
        "message": workflow_progress_message(_pl, "startup"),
        "results": {},
        "error": None,
        "preferred_lang": _pl,
    }
    logger.info(f"✅ Workflow state initialized: {workflow_id}")

    async def schedule_workflow():
        # Run Agent 1 validation, then run Agents 2→3→4.
        # Keep all progress/error updates in-memory under workflow_state.
        if workflow_id not in workflow_state:
            return
        state = workflow_state[workflow_id]
        pl = request.preferred_lang or "en"

        try:
            state["message"] = workflow_progress_message(pl, "agent1_validate")
            # IMPORTANT: run agent1 validation in executor so it doesn't block the event loop.
            loop = asyncio.get_running_loop()
            agent1_result = await loop.run_in_executor(
                None,
                agent1.validate_inputs,
                request.resume_text,
                request.projects_text,
            )

            if not agent1_result.get("is_valid", False):
                issues = agent1_result.get("issues") or []
                if not issues and agent1_result.get("validation_summary"):
                    issues = [agent1_result["validation_summary"]]
                if not issues:
                    issues = ["Resume or required sections are incomplete. Please add work/internship experience and education."]

                logger.info(f"❌ Validation failed: {issues}")
                state["status"] = "failed"
                state["error"] = "; ".join(str(x) for x in issues[:3])
                state["results"]["agent1"] = agent1_result
                state["current_step"] = "completed"
                state["progress"] = 100
                return

            state["results"]["agent1"] = agent1_result
            state["progress"] = 5
            state["current_step"] = "agent2"
            state["message"] = workflow_progress_message(pl, "agent2_after_validation")

            await execute_workflow_async(
                workflow_id,
                jd_text=request.jd_text,
                resume_text=request.resume_text,
                projects_text=request.projects_text,
                job_title=request.job_title,
                company_name=request.company_name,
                country_or_region=request.country_or_region,
                preferred_lang=pl,
            )

        except Exception as e:
            logger.error(f"❌ Error in schedule_workflow for {workflow_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            if workflow_id in workflow_state:
                workflow_state[workflow_id]["status"] = "failed"
                workflow_state[workflow_id]["error"] = str(e)

    try:
        asyncio.create_task(schedule_workflow())
    except Exception as e:
        logger.error(f"❌ Failed to create task: {str(e)}")
        background_tasks.add_task(
            schedule_workflow,
        )

    return {
        "status": "started",
        "workflow_id": workflow_id,
        "message": "Workflow started. Use /api/v1/workflow/progress/{workflow_id} to track progress."
    }


@app.get("/api/v1/workflow/progress/{workflow_id}")
async def get_workflow_progress(workflow_id: str) -> Dict:
    """Get current workflow progress. Includes workflow_found so frontend can detect wrong backend or multi-worker."""
    logger = logging.getLogger(__name__)
    # First check if workflow is in active state
    if workflow_id in workflow_state:
        out = dict(workflow_state[workflow_id])
        out["workflow_found"] = True
        logger.debug(f"Progress {workflow_id}: found in state, progress={out.get('progress')}, step={out.get('current_step')}")
        return out

    # If not in active state, check if it's in results (completed workflows)
    if workflow_id in workflow_results:
        result_data = workflow_results[workflow_id]
        logger.debug(f"Progress {workflow_id}: found in results (completed)")
        _pl_done = result_data.get("preferred_lang") or "en"
        return {
            "status": "completed",
            "current_step": "completed",
            "progress": 100,
            "message": workflow_progress_message(_pl_done, "completed_poll"),
            "preferred_lang": _pl_done,
            "results": {
                "agent1": result_data.get("agent1_result", {}),
                "agent2": result_data.get("agent2_outputs", {}),
                "agent3": result_data.get("agent3_outputs", {}),
                "agent4": result_data.get("agent4_outputs", {}),
                "agent5": result_data.get("agent5_outputs", {}),
            },
            "error": None,
            "workflow_found": True,
        }

    # Workflow not found in this process - likely frontend hitting different backend or multi-worker
    logger.warning(f"Progress {workflow_id}: NOT FOUND in this process (workflow_state has {len(workflow_state)} entries). "
                   "Frontend may be polling a different backend instance. Use single uvicorn worker (default).")
    return {
        "status": "running",
        "current_step": "agent1",
        "progress": 0,
        "message": "Workflow is initializing...",
        "results": {},
        "error": None,
        "workflow_found": False,
    }


@app.get("/api/v1/workflow/progress/{workflow_id}/stream")
async def stream_workflow_progress(workflow_id: str):
    """
    Stream workflow progress using Server-Sent Events (SSE).
    Note: Some proxies/gateways may not support SSE, so polling fallback is recommended.
    """
    async def event_generator():
        try:
            # Send initial connection message
            yield f": SSE connection established\n\n"
            
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
            last_state = None
            max_iterations = 600  # Maximum 10 minutes (600 seconds)
            iteration = 0
            initial_sent = False
            
            while iteration < max_iterations:
                # Check if workflow exists
                if workflow_id not in workflow_state:
                    # Workflow was removed, send final state if we have it
                    if last_state:
                        yield f"data: {json.dumps(last_state)}\n\n"
                    break
                
                state = workflow_state[workflow_id]
                
                # Always send initial state immediately
                if not initial_sent:
                    yield f"data: {json.dumps(state)}\n\n"
                    last_state = state
                    initial_sent = True
                # Send if state changed
                elif state != last_state:
                    yield f"data: {json.dumps(state)}\n\n"
                    last_state = state
                
                # If completed or failed, send final state multiple times and break
                if state["status"] in ["completed", "failed"]:
                    # Send final state multiple times to ensure it's received
                    for _ in range(3):
                        yield f"data: {json.dumps(state)}\n\n"
                        await asyncio.sleep(0.5)
                    break
                
                iteration += 1
                await asyncio.sleep(1)  # Update every second
            
            # Final check: if workflow still exists and we haven't sent final state, send it
            if workflow_id in workflow_state:
                final_state = workflow_state[workflow_id]
                if final_state != last_state:
                    yield f"data: {json.dumps(final_state)}\n\n"
                await asyncio.sleep(1)  # Give client time to receive
        except Exception as e:
            # Send error message before closing
            error_state = {
                "status": "failed",
                "error": f"SSE stream error: {str(e)}",
                "message": "Connection error occurred"
            }
            yield f"data: {json.dumps(error_state)}\n\n"
    
    # Add headers for SSE compatibility
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disable buffering in nginx
    }
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers=headers
    )


def _run_workflow_sync(
    workflow_id: str,
    jd_text: str,
    resume_text: str,
    projects_text: Optional[str],
    job_title: str = "",
    company_name: str = "",
    country_or_region: Optional[str] = None,
    preferred_lang: str = "en",
) -> None:
    """
    Synchronous workflow runner (Agent 2 → 3 → 4). Intended to be run in a thread pool
    so the event loop can still serve /workflow/progress and other requests.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🔄 _run_workflow_sync started: {workflow_id}")

        if workflow_id not in workflow_state:
            logger.error(f"❌ Workflow {workflow_id} not found in state")
            return

        state = workflow_state[workflow_id]
        pl = preferred_lang or "en"
        if "preferred_lang" not in state:
            state["preferred_lang"] = pl
        agent1_result = state.get("results", {}).get("agent1") or {
            "is_valid": True,
            "has_work_experience": True,
            "has_education": True,
            "has_project_materials": bool(projects_text),
            "validation_summary": "Validation passed",
            "issues": []
        }

        # ── Agent 2: JD Analysis ──
        state["current_step"] = "agent2"
        state["progress"] = 10
        state["message"] = workflow_progress_message(pl, "agent2_prep")
        import time as _time
        _t0 = _time.time()
        state["progress"] = 15
        state["message"] = workflow_progress_message(pl, "agent2_analyzing")
        try:
            agent2_result = agent2.analyze_jd_and_match(
                jd_text=jd_text,
                resume_text=resume_text,
                project_materials=projects_text,
                fast_mode=AGENT2_FAST_MODE,
                parallel_20s=True,
                job_title=job_title or None,
                company_name=company_name or None,
                country_or_region=country_or_region,
                preferred_lang=pl,
            )
            if not agent2_result.get("job_role_team_analysis") and not agent2_result.get("ideal_candidate_profile"):
                logger.warning(f"Agent 2 output missing critical fields, but continuing...")
            state["results"]["agent2"] = agent2_result
            state["progress"] = 30
            state["message"] = "JD 分析完成"
            logger.info(f"Agent 2 completed in {_time.time()-_t0:.1f}s")
        except Exception as e:
            import traceback
            error_msg = f"Agent 2 error: {str(e)}"
            logger.error(f"Agent 2 failed: {error_msg}\n{traceback.format_exc()}")
            state["status"] = "failed"
            state["error"] = error_msg
            return

        # ── Agent 3: Project Packaging ──
        _read_timeout = 30.0 if AGENT2_FAST_MODE else None
        state["current_step"] = "agent3"
        state["progress"] = 32
        has_project_materials = bool(projects_text and str(projects_text).strip())
        if not has_project_materials:
            state["message"] = workflow_progress_message(pl, "agent3_skip")
            agent3_result = {
                "skipped": True,
                "reason": "no_project_materials",
                "message": workflow_progress_message(pl, "agent3_skip_detail"),
                "selected_projects": [],
                "skipped_projects": [],
            }
            state["results"]["agent3"] = agent3_result
            state["progress"] = 35
            logger.info(f"Agent 3 skipped (no project materials)")
        else:
            state["message"] = workflow_progress_message(pl, "agent3_running")
            _t3 = _time.time()
            try:
                agent3_result = agent3.package_projects(
                    jd_text=jd_text,
                    project_materials=projects_text or "",
                    agent2_outputs=agent2_result,
                    read_timeout_sec=_read_timeout,
                    preferred_lang=pl,
                )
                if "selected_projects" not in agent3_result:
                    agent3_result["selected_projects"] = []
                state["results"]["agent3"] = agent3_result
                state["progress"] = 35
                logger.info(f"Agent 3 completed in {_time.time()-_t3:.1f}s")
            except Exception as e:
                import traceback
                error_msg = f"Agent 3 error: {str(e)}"
                logger.error(f"Agent 3 failed: {error_msg}\n{traceback.format_exc()}")
                state["status"] = "failed"
                state["error"] = error_msg
                return

        # ── Agent 4: Resume Optimization ──
        state["current_step"] = "agent4"
        state["progress"] = 38
        state["message"] = workflow_progress_message(pl, "agent4_gen")
        _t4 = _time.time()
        try:
            optimization_service.load_original_resume(resume_text)
            optimization_service.load_agent3_outputs(agent3_result)
            state["progress"] = 42
            state["message"] = workflow_progress_message(pl, "agent4_gap")
            # Agent 4: full Agent 2 + Agent 3 context for JD-vs-bullet alignment; longer timeout so every
            # experience bullet can get a suggestion (fast workflow timers are too tight for complete JSON).
            _agent4_timeout = None if not AGENT2_FAST_MODE else 420.0
            agent4_result = agent4.optimize_resume(
                jd_text=jd_text,
                resume_text=resume_text,
                agent2_outputs=agent2_result,
                agent3_outputs=agent3_result,
                read_timeout_sec=_agent4_timeout,
                fast_run=False,
                jd_resume_only=False,
                use_condensed_jd=True,
                preferred_lang=pl,
            )
            agent4_result["experience_replacements"] = []
            if "format_content_adjustments" not in agent4_result:
                agent4_result["format_content_adjustments"] = []
            if "experience_optimizations" not in agent4_result:
                agent4_result["experience_optimizations"] = []
            optimization_service.load_optimization_recommendations(agent4_result)
            state["results"]["agent4"] = agent4_result
            state["progress"] = 55
            state["message"] = "简历优化建议生成完成"
            logger.info(f"Agent 4 completed in {_time.time()-_t4:.1f}s")
        except Exception as e:
            import traceback
            error_msg = f"Agent 4 error: {str(e)}"
            logger.error(f"Agent 4 failed: {error_msg}\n{traceback.format_exc()}")
            state["status"] = "failed"
            state["error"] = error_msg
            return

        # ── Generate final resume (auto-accept all suggestions) ──
        state["progress"] = 58
        state["message"] = workflow_progress_message(pl, "resume_final")
        try:
            final_result = optimization_service.apply_feedback_and_generate_resume()
            final_resume = final_result.get("final_resume", resume_text)
            classified_projects = final_result.get("classified_projects", {})
        except Exception as e:
            logger.warning(f"Failed to generate final resume, using original: {e}")
            final_resume = resume_text
            classified_projects = {}

        # ── Agent 5: Interview Preparation ──
        agent5_result = None
        if not AGENT5_DISABLED:
            state["current_step"] = "agent5"
            state["progress"] = 62
            state["message"] = workflow_progress_message(pl, "agent5_gen")
            _t5 = _time.time()
            try:
                state["progress"] = 68
                state["message"] = workflow_progress_message(pl, "agent5_analyze")
                agent4_for_agent5 = {
                    "final_resume": final_resume,
                    "classified_projects": classified_projects,
                    "optimized_work_experiences": final_result.get("optimized_work_experiences", []) if 'final_result' in dir() else [],
                    "optimized_project_documents": final_result.get("optimized_project_documents", []) if 'final_result' in dir() else [],
                }
                agent5_result = agent5.prepare_interview(
                    jd_text=jd_text,
                    final_resume=final_resume,
                    agent2_outputs=agent2_result,
                    agent4_outputs=agent4_for_agent5,
                    read_timeout_sec=60.0,
                    fast_run=AGENT2_FAST_MODE,
                    preferred_lang=pl,
                )
                state["results"]["agent5"] = agent5_result
                state["progress"] = 90
                state["message"] = workflow_progress_message(pl, "agent5_done")
                logger.info(f"Agent 5 completed in {_time.time()-_t5:.1f}s")
            except Exception as e:
                import traceback
                logger.warning(f"Agent 5 failed (non-fatal): {str(e)}\n{traceback.format_exc()}")
                state["results"]["agent5"] = {"error": str(e), "skipped": True}
                state["progress"] = 90
        else:
            state["progress"] = 90
            logger.info("Agent 5 disabled, skipping interview prep")

        workflow_results[workflow_id] = {
            "jd_text": jd_text,
            "resume_text": resume_text,
            "agent2_outputs": agent2_result,
            "agent3_outputs": agent3_result,
            "agent4_outputs": agent4_result,
            "agent1_result": agent1_result,
            "agent5_outputs": agent5_result or {},
            "final_resume": final_resume,
            "preferred_lang": pl,
        }
        state["current_step"] = "completed"
        state["progress"] = 100
        state["status"] = "completed"
        state["message"] = workflow_progress_message(pl, "workflow_done")
        logger.info(f"Workflow {workflow_id} completed successfully (total {_time.time()-_t0:.1f}s)")

    except Exception as e:
        import traceback
        error_msg = f"Workflow error: {str(e)}"
        logger.error(f"Workflow execution failed: {error_msg}\n{traceback.format_exc()}")
        if workflow_id in workflow_state:
            workflow_state[workflow_id]["status"] = "failed"
            workflow_state[workflow_id]["error"] = error_msg


async def execute_workflow_async(
    workflow_id: str,
    jd_text: str,
    resume_text: str,
    projects_text: Optional[str],
    job_title: str = "",
    company_name: str = "",
    country_or_region: Optional[str] = None,
    preferred_lang: str = "en",
) -> None:
    """
    Run workflow in a thread pool so the event loop stays free to serve
    /workflow/progress and other requests (avoid ETIMEDOUT on progress polling).
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        _run_workflow_sync,
        workflow_id,
        jd_text,
        resume_text,
        projects_text,
        job_title,
        company_name,
        country_or_region,
        preferred_lang,
    )


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


@app.post("/api/v1/resume/regenerate-suggestion")
async def regenerate_suggestion(request: RegenerateSuggestionRequest) -> Dict:
    """
    Natural language feedback (regenerate with user instruction) is temporarily disabled.
    Use structured feedback: accept, reject, or further_modify with modified_text (user's own revised bullet).
    """
    raise HTTPException(
        status_code=410,
        detail="Natural language feedback is disabled. Use submit_feedback with feedback='accept', 'reject', or 'further_modify' with modified_text."
    )


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

    workflow_data = workflow_results[request.workflow_id]
    _ipl = workflow_data.get("preferred_lang") or "en"

    interview_id = f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    workflow_state[interview_id] = {
        "status": "running",
        "progress": 0,
        "message": workflow_progress_message(_ipl, "interview_prep"),
        "result": None,
        "error": None,
        "preferred_lang": _ipl,
    }

    # Use final resume already produced by POST /api/v1/resume/generate (or workflow).
    # Do NOT call apply_feedback_and_generate_resume() again here — it repeats heavy work and
    # often exceeds the frontend axios timeout (30s), breaking interview start on deploy.
    handoff = optimization_service.build_agent4_outputs_for_interview_prep()
    if "error" in handoff:
        raise HTTPException(status_code=400, detail=handoff["error"])

    final_resume = handoff["final_resume"]
    agent4_outputs = {
        "final_resume": final_resume,
        "classified_projects": handoff.get("classified_projects", {}),
        "optimized_work_experiences": handoff.get("optimized_work_experiences", []),
        "optimized_project_documents": handoff.get("optimized_project_documents", []),
    }
    
    background_tasks.add_task(
        execute_interview_prep_async,
        interview_id,
        workflow_data["jd_text"],
        final_resume,
        workflow_data["agent2_outputs"],
        agent4_outputs,
        _ipl,
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
    agent4_outputs: Dict,  # Now includes full Agent 4 output
    preferred_lang: str = "en",
):
    """Execute Agent 5 in background."""
    try:
        state = workflow_state[interview_id]
        pl = preferred_lang or "en"

        state["progress"] = 30
        state["message"] = workflow_progress_message(pl, "interview_generating")

        # Execute Agent 5 with complete Agent 4 outputs (fast_run when AGENT2_FAST_MODE for ~30s total)
        from config import AGENT2_FAST_MODE as _fast
        agent5_result = agent5.prepare_interview(
            jd_text=jd_text,
            final_resume=final_resume,
            agent2_outputs=agent2_outputs,
            agent4_outputs=agent4_outputs,
            read_timeout_sec=120.0,
            fast_run=_fast,
            preferred_lang=pl,
        )

        state["progress"] = 100
        state["status"] = "completed"
        state["result"] = agent5_result
        state["message"] = workflow_progress_message(pl, "interview_done")
        
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

def _safe_download_filename(name: str, ext: str) -> str:
    base = re.sub(r"[^\w\-.]+", "_", (name or "export").strip())[:120]
    return f"{base or 'export'}.{ext}"


@app.post("/api/v1/resume/export")
async def export_resume(request: ExportRequest):
    """Export final resume to PDF or DOCX. Returns file bytes (no temp file on disk)."""
    try:
        if not optimization_service.final_resume:
            raise HTTPException(status_code=400, detail="Final resume not available")
        fmt = (request.format or "pdf").lower()
        title = request.title or "Resume"
        if fmt == "pdf":
            result = exporter.export_plain_text_pdf_bytes(optimization_service.final_resume, title)
        elif fmt == "docx":
            result = exporter.export_plain_text_docx_bytes(optimization_service.final_resume, title)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format; use pdf or docx")
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        fname = _safe_download_filename(title, fmt)
        media = (
            "application/pdf"
            if fmt == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return StreamingResponse(
            io.BytesIO(result["data"]),
            media_type=media,
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting resume: {str(e)}")


@app.post("/api/v1/export/text-document")
async def export_text_document(request: ExportTextDocumentRequest):
    """Export client-provided plain text as PDF (full interview prep, etc.)."""
    try:
        fmt = (request.format or "pdf").lower()
        if fmt != "pdf":
            raise HTTPException(status_code=400, detail="Only pdf is supported for text-document export")
        text = request.text or ""
        if len(text) > MAX_TEXT_DOCUMENT_EXPORT_CHARS:
            raise HTTPException(status_code=400, detail="Content too large for export")
        title = request.title or "Interview_Prep"
        result = exporter.export_plain_text_pdf_bytes(text, title)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        fname = _safe_download_filename(title, "pdf")
        return StreamingResponse(
            io.BytesIO(result["data"]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting document: {str(e)}")


class ExportProjectsRequest(BaseModel):
    format: str = "pdf"


def _build_projects_text() -> str:
    """Build plain text from classified projects for export."""
    cp = optimization_service.get_classified_projects_for_interview()
    lines = ["Project Materials (Resume Adopted / Not Adopted)", "=" * 50, ""]
    for label, key in [("Resume Adopted Projects", "resume_adopted_projects"), ("Resume Not Adopted Projects", "resume_not_adopted_projects")]:
        lines.append(f"=== {label} ===")
        for i, p in enumerate(cp.get(key, []), 1):
            lines.append(f"\nProject {i}: {p.get('project_name', 'Unnamed')}")
            if p.get("summary"):
                lines.append(p["summary"])
            for b in p.get("resume_summary_bullets", []) or []:
                lines.append(f"  • {b}")
            lines.append("")
        lines.append("")
    return "\n".join(lines)


@app.post("/api/v1/export/projects")
async def export_projects(request: ExportProjectsRequest):
    """Export project materials (classified projects) to PDF or DOCX. Returns file attachment."""
    try:
        text = _build_projects_text()
        if not text.strip():
            raise HTTPException(status_code=400, detail="No project materials available. Generate final resume first.")
        os.makedirs("data/exports", exist_ok=True)
        path = f"data/exports/projects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}"
        result = exporter.export(resume_text=text, output_path=path, format=request.format, title="Project_Materials")
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return FileResponse(
            path,
            filename=f"Project_Materials.{request.format}",
            media_type="application/pdf" if request.format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ExportInterviewRequest(BaseModel):
    interview_id: str
    format: str = "pdf"


def _build_interview_text(result: Dict) -> str:
    """Build plain text from Agent 5 interview result."""
    lines = ["Interview Preparation", "=" * 50, ""]
    # Theme keys used by Agent 5
    for theme_key in ["theme_1_behavioral_interview", "theme_2_project_deep_dive", "theme_3_business_domain"]:
        theme = result.get(theme_key)
        if not theme:
            continue
        title = theme.get("title") or theme_key.replace("_", " ").title()
        lines.append(f"=== {title} ===")
        lines.append("")
        for k, v in theme.items():
            if k == "title" or not v:
                continue
            if isinstance(v, str):
                lines.append(f"{k}:\n{v}\n")
            elif isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  • {item}" if isinstance(item, str) else f"  • {json.dumps(item, ensure_ascii=False)[:300]}")
                lines.append("")
            else:
                lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)[:500]}\n")
        lines.append("")
    # Interview rounds (recruiter / HM / leader)
    rounds = result.get("theme_rounds") or {}
    for round_key in ["recruiter_round", "hiring_manager_round", "leader_round"]:
        r = rounds.get(round_key)
        if not r:
            continue
        lines.append(f"=== {r.get('round_name', round_key)} ===")
        for q in r.get("typical_questions", []):
            lines.append(f"Q: {q.get('question', '')}")
            lines.append(f"Why: {q.get('why_asked', '')}")
            lines.append(f"Framework: {q.get('answer_framework', '')}")
            lines.append("")
        lines.append("")
    return "\n".join(lines)


@app.post("/api/v1/export/interview")
async def export_interview(request: ExportInterviewRequest):
    """Export interview preparation to PDF or DOCX. Returns file attachment."""
    try:
        if request.interview_id not in workflow_state:
            raise HTTPException(status_code=404, detail="Interview not found")
        state = workflow_state[request.interview_id]
        if state.get("status") != "completed" or not state.get("result"):
            raise HTTPException(status_code=400, detail="Interview result not ready")
        text = _build_interview_text(state["result"])
        os.makedirs("data/exports", exist_ok=True)
        path = f"data/exports/interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}"
        result = exporter.export(resume_text=text, output_path=path, format=request.format, title="Interview_Prep")
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return FileResponse(
            path,
            filename=f"Interview_Prep.{request.format}",
            media_type="application/pdf" if request.format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
