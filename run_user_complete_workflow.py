"""Complete Application Run with User's Actual Data."""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from agent1 import InputValidationAgent
from agent2 import JDAnalysisAgent
from agent3 import ProjectPackagingAgent
from agent4 import ResumeOptimizationAgent
from agent5 import InterviewPreparationAgent
from resume_optimization_service import ResumeOptimizationService
from resume_export import ResumeExporter


def main():
    """Run complete workflow with user's data."""
    print("="*80)
    print("AI Job Hunting Assistant - Complete Application Run")
    print("="*80)
    print()
    print("Please provide your data. You can:")
    print("1. Place files in data/ directory:")
    print("   - data/resumes/resume.txt")
    print("   - data/jobs/jd.txt")
    print("   - data/projects/projects.txt (optional)")
    print()
    print("2. Or paste directly when prompted")
    print()
    
    # Try to load from files
    data_dir = Path(__file__).parent / "data"
    resume_file = None
    jd_file = None
    project_file = None
    
    # Check for resume
    for ext in [".txt", ".md"]:
        potential = data_dir / "resumes" / f"resume{ext}"
        if potential.exists():
            resume_file = potential
            break
    
    # Check for JD
    for ext in [".txt", ".md"]:
        potential = data_dir / "jobs" / f"jd{ext}"
        if potential.exists():
            jd_file = potential
            break
        # Also check for any .txt/.md in jobs folder
        for f in (data_dir / "jobs").glob(f"*{ext}"):
            jd_file = f
            break
    
    # Check for projects
    for ext in [".txt", ".md"]:
        potential = data_dir / "projects" / f"projects{ext}"
        if potential.exists():
            project_file = potential
            break
        for f in (data_dir / "projects").glob(f"*{ext}"):
            project_file = f
            break
    
    # Load or prompt for resume
    if resume_file:
        print(f"📄 Found resume: {resume_file.name}")
        resume_text = resume_file.read_text(encoding='utf-8')
    else:
        print("📄 Resume file not found. Please paste your resume:")
        print("   (Press Enter twice when done)")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        resume_text = "\n".join(lines[:-1])  # Remove last empty line
    
    # Load or prompt for JD
    if jd_file:
        print(f"📋 Found JD: {jd_file.name}")
        jd_text = jd_file.read_text(encoding='utf-8')
    else:
        print("\n📋 JD file not found. Please paste the job description:")
        print("   (Press Enter twice when done)")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        jd_text = "\n".join(lines[:-1])
    
    # Load or prompt for projects
    if project_file:
        print(f"📁 Found projects: {project_file.name}")
        project_materials = project_file.read_text(encoding='utf-8')
    else:
        print("\n📁 Project materials (optional). Paste if available:")
        print("   (Press Enter twice when done, or just Enter to skip)")
        lines = []
        while True:
            line = input()
            if line == "" and (not lines or lines[-1] == ""):
                break
            lines.append(line)
        project_materials = "\n".join(lines[:-1]) if len(lines) > 1 else None
    
    print("\n" + "="*80)
    print("🚀 Starting Complete Workflow")
    print("="*80)
    print()
    
    # Step 1: Validation
    print("Step 1/5: Input Validation...")
    agent1 = InputValidationAgent()
    agent1_result = agent1.validate_inputs(resume_text, project_materials)
    if not agent1_result.get('is_valid'):
        print(f"❌ Validation failed: {agent1_result.get('validation_summary')}")
        return
    print("✅ Validation passed")
    print()
    
    # Step 2: JD Analysis
    print("Step 2/5: JD Analysis & Matching (this may take 30-60 seconds)...")
    agent2 = JDAnalysisAgent()
    agent2_outputs = agent2.analyze_jd_and_match(jd_text, resume_text, project_materials)
    if "error" in agent2_outputs:
        print(f"❌ Analysis failed: {agent2_outputs['error']}")
        return
    match_score = agent2_outputs.get("match_assessment", {}).get("overall_match_score", "N/A")
    print(f"✅ Analysis complete - Match Score: {match_score}/5.0")
    print()
    
    # Step 3: Project Packaging
    if project_materials:
        print("Step 3/5: Project Packaging (this may take 30-60 seconds)...")
        agent3 = ProjectPackagingAgent()
        agent3_outputs = agent3.package_projects(jd_text, project_materials, agent2_outputs)
        if "error" in agent3_outputs:
            print(f"⚠️  Packaging error: {agent3_outputs['error']}")
            agent3_outputs = {"selected_projects": [], "skipped_projects": []}
        else:
            print(f"✅ Packaging complete - {len(agent3_outputs.get('selected_projects', []))} projects selected")
    else:
        print("Step 3/5: Project Packaging - Skipped (no project materials)")
        agent3_outputs = {"selected_projects": [], "skipped_projects": []}
    print()
    
    # Step 4: Resume Optimization
    print("Step 4/5: Resume Optimization (this may take 30-60 seconds)...")
    agent4 = ResumeOptimizationAgent()
    recommendations = agent4.optimize_resume(jd_text, resume_text, agent2_outputs, agent3_outputs)
    
    service = ResumeOptimizationService()
    service.load_original_resume(resume_text)
    service.load_agent3_outputs(agent3_outputs)
    service.load_optimization_recommendations(recommendations)
    
    # Accept all replacements for demo
    for idx in range(len(recommendations.get("experience_replacements", []))):
        service.submit_feedback("experience_replacement", f"replacement_{idx}", "accept")
    
    final_result = service.apply_feedback_and_generate_resume()
    if "error" in final_result:
        print(f"❌ Error: {final_result['error']}")
        return
    
    print(f"✅ Optimization complete - {final_result.get('total_modifications', 0)} modifications applied")
    print()
    
    # Step 5: Interview Preparation
    print("Step 5/5: Interview Preparation (this may take 60-90 seconds)...")
    agent5 = InterviewPreparationAgent()
    agent5_outputs = agent5.prepare_interview(
        jd_text,
        final_result["final_resume"],
        agent2_outputs,
        {"classified_projects": final_result["classified_projects"]}
    )
    
    theme1 = agent5_outputs.get("theme_1_behavioral_interview", {})
    theme2 = agent5_outputs.get("theme_2_project_deep_dive", {})
    theme3 = agent5_outputs.get("theme_3_business_domain", {})
    print(f"✅ Interview prep complete:")
    print(f"   - Behavioral questions: {len(theme1.get('top_10_behavioral_questions', []))}")
    print(f"   - Projects analyzed: {len(theme2.get('selected_projects', []))}")
    print(f"   - Business questions: {len(theme3.get('business_questions', []))}")
    print()
    
    # Save outputs
    output_dir = data_dir / "outputs"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    outputs = {
        "agent1": agent1_result,
        "agent2": agent2_outputs,
        "agent3": agent3_outputs,
        "agent4_recommendations": recommendations,
        "final_resume": final_result["final_resume"],
        "classified_projects": final_result["classified_projects"],
        "agent5": agent5_outputs
    }
    
    # Save JSON
    with open(output_dir / f"complete_output_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2, ensure_ascii=False)
    
    # Save final resume text
    with open(output_dir / f"final_resume_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write(final_result["final_resume"])
    
    # Export PDF/DOCX
    exporter = ResumeExporter()
    try:
        exporter.export_to_pdf(final_result["final_resume"], str(output_dir / f"final_resume_{timestamp}.pdf"))
        exporter.export_to_docx(final_result["final_resume"], str(output_dir / f"final_resume_{timestamp}.docx"))
        print("✅ Resume exported to PDF and DOCX")
    except Exception as e:
        print(f"⚠️  Export error: {e}")
    
    print()
    print("="*80)
    print("✅ COMPLETE - All Outputs Generated!")
    print("="*80)
    print(f"\n📁 Output files saved to: data/outputs/")
    print(f"   • complete_output_{timestamp}.json")
    print(f"   • final_resume_{timestamp}.txt")
    print(f"   • final_resume_{timestamp}.pdf")
    print(f"   • final_resume_{timestamp}.docx")
    print()


if __name__ == "__main__":
    main()
