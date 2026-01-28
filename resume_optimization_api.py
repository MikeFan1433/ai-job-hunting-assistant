"""API endpoints for Resume Optimization Service."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from resume_optimization_service import ResumeOptimizationService
from resume_export import ResumeExporter
from agent4 import ResumeOptimizationAgent

app = FastAPI(title="Resume Optimization API", version="1.0.0")

# Global service instances
optimization_service = ResumeOptimizationService()
exporter = ResumeExporter()
agent4 = ResumeOptimizationAgent()


class OptimizationRequest(BaseModel):
    """Request model for resume optimization."""
    jd_text: str
    resume_text: str
    agent2_outputs: Dict
    agent3_outputs: Dict


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    feedback_type: str  # "experience_replacement", "format_adjustment", "experience_optimization", or "skills_optimization"
    item_id: str  # Unique identifier for the item (for skills_optimization, can be "skills_section")
    feedback: str  # "accept", "further_modify", or "reject"
    additional_notes: Optional[str] = None


class ExportRequest(BaseModel):
    """Request model for resume export."""
    format: str = "pdf"  # "pdf" or "docx"
    title: str = "Resume"


@app.post("/api/v1/resume/optimize")
async def optimize_resume(request: OptimizationRequest) -> Dict:
    """
    Get optimization recommendations from Agent 4.
    
    Returns:
        Dictionary with optimization recommendations including project classification
    """
    try:
        # Load original resume
        optimization_service.load_original_resume(request.resume_text)
        
        # Load Agent 3 outputs for project classification
        optimization_service.load_agent3_outputs(request.agent3_outputs)
        
        # Get optimization recommendations from Agent 4
        recommendations = agent4.optimize_resume(
            jd_text=request.jd_text,
            resume_text=request.resume_text,
            agent2_outputs=request.agent2_outputs,
            agent3_outputs=request.agent3_outputs
        )
        
        # Load recommendations into service
        optimization_service.load_optimization_recommendations(recommendations)
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "feedback_status": optimization_service.get_feedback_status(),
            "project_classification": recommendations.get("project_classification", {
                "resume_adopted_projects": [],
                "resume_not_adopted_projects": []
            })
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing resume: {str(e)}")


@app.post("/api/v1/resume/feedback")
async def submit_feedback(request: FeedbackRequest) -> Dict:
    """
    Submit user feedback for a specific optimization recommendation.
    
    Returns:
        Dictionary with feedback confirmation
    """
    try:
        result = optimization_service.submit_feedback(
            feedback_type=request.feedback_type,
            item_id=request.item_id,
            feedback=request.feedback,
            additional_notes=request.additional_notes
        )
        
        return {
            "status": "success",
            "feedback_result": result,
            "feedback_status": optimization_service.get_feedback_status()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@app.get("/api/v1/resume/feedback/status")
async def get_feedback_status() -> Dict:
    """
    Get current status of user feedback.
    
    Returns:
        Dictionary with feedback status
    """
    try:
        return {
            "status": "success",
            "feedback_status": optimization_service.get_feedback_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting feedback status: {str(e)}")


@app.post("/api/v1/resume/generate")
async def generate_final_resume() -> Dict:
    """
    Apply all user feedback and generate the final optimized resume.
    Also updates project classification.
    
    Returns:
        Dictionary with final resume, modification summary, and project classification
    """
    try:
        result = optimization_service.apply_feedback_and_generate_resume()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "final_resume": result["final_resume"],  # 1. 最终优化后的简历
            "classified_projects": result.get("classified_projects", {  # 2. 经过采纳分类后的项目文本（包含完整项目详情）
                "resume_adopted_projects": [],
                "resume_not_adopted_projects": []
            }),
            "modifications_applied": result["modifications_applied"],
            "summary": result["summary"],
            "project_classification": result.get("project_classification", {  # 分类摘要（索引和名称）
                "resume_adopted_projects": [],
                "resume_not_adopted_projects": []
            })
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating final resume: {str(e)}")


@app.post("/api/v1/resume/export")
async def export_resume(request: ExportRequest) -> Dict:
    """
    Export final resume to PDF or Word format.
    
    Returns:
        Dictionary with export status and file path
    """
    try:
        # Get final resume
        if not optimization_service.final_resume:
            # Try to generate if not already generated
            generate_result = optimization_service.apply_feedback_and_generate_resume()
            if "error" in generate_result:
                raise HTTPException(status_code=400, detail="Final resume not available. Please generate it first.")
        
        # Export resume
        output_path = f"data/resumes/final_resume.{request.format}"
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


@app.get("/api/v1/resume/recommendations")
async def get_recommendations() -> Dict:
    """
    Get current optimization recommendations.
    
    Returns:
        Dictionary with current recommendations and project classification
    """
    try:
        if not optimization_service.optimization_recommendations:
            raise HTTPException(status_code=404, detail="No recommendations available. Please optimize resume first.")
        
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


@app.get("/api/v1/projects/classified")
async def get_classified_projects() -> Dict:
    """
    Get classified projects organized for interview preparation.
    
    Returns:
        Dictionary with resume_adopted and resume_not_adopted projects with full details
    """
    try:
        classified_projects = optimization_service.get_classified_projects_for_interview()
        
        return {
            "status": "success",
            "classified_projects": classified_projects,
            "summary": {
                "resume_adopted_count": len(classified_projects.get("resume_adopted_projects", [])),
                "resume_not_adopted_count": len(classified_projects.get("resume_not_adopted_projects", []))
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting classified projects: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Resume Optimization API",
        "version": "1.0.0",
        "endpoints": {
            "optimize": "/api/v1/resume/optimize",
            "submit_feedback": "/api/v1/resume/feedback",
            "get_feedback_status": "/api/v1/resume/feedback/status",
            "generate_final": "/api/v1/resume/generate",
            "export": "/api/v1/resume/export",
            "get_recommendations": "/api/v1/resume/recommendations"
        }
    }
