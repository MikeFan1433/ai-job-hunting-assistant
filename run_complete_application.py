"""Complete Application Run - Generate all outputs for user's resume, JD, and projects."""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent1 import InputValidationAgent
from agent2 import JDAnalysisAgent
from agent3 import ProjectPackagingAgent
from agent4 import ResumeOptimizationAgent
from agent5 import InterviewPreparationAgent
from resume_optimization_service import ResumeOptimizationService
from resume_export import ResumeExporter


def load_user_data():
    """
    Load user's resume, JD, and project materials.
    Try to load from files, or prompt user to provide them.
    """
    # Try to load from files first
    data_dir = Path(__file__).parent / "data"
    
    # Check for resume file
    resume_files = list((data_dir / "resumes").glob("*.txt")) + \
                   list((data_dir / "resumes").glob("*.md"))
    
    # Check for JD file
    jd_files = list((data_dir / "jobs").glob("*.txt")) + \
               list((data_dir / "jobs").glob("*.md"))
    
    # Check for project files
    project_files = list((data_dir / "projects").glob("*.txt")) + \
                    list((data_dir / "projects").glob("*.md"))
    
    resume_text = None
    jd_text = None
    project_materials = None
    
    # Load resume
    if resume_files:
        print(f"📄 Found resume file: {resume_files[0].name}")
        resume_text = resume_files[0].read_text(encoding='utf-8')
    else:
        print("⚠️  No resume file found. Please provide resume text.")
        print("   Expected location: data/resumes/resume.txt")
        # For now, use sample - user can replace
        resume_text = input("Please paste your resume text (or press Enter to use sample): ").strip()
        if not resume_text:
            print("Using sample resume...")
            resume_text = """BOYANG (MIKE) FAN
Email: mike.fan@email.com | Phone: (555) 123-4567

WORK EXPERIENCE

Data Scientist | Tech Company | 2020-2023
• Developed machine learning models for business applications
• Worked on AI projects and improved customer experience
• Analyzed data and created predictive models
• Presented findings to stakeholders

Data Analyst | Analytics Corp | 2018-2020
• Performed data analysis and created reports
• Worked with SQL and Python for data processing
• Collaborated with cross-functional teams

EDUCATION

Master of Science in Data Science | University Name | 2018
Bachelor of Science in Statistics | University Name | 2016"""
    
    # Load JD
    if jd_files:
        print(f"📋 Found JD file: {jd_files[0].name}")
        jd_text = jd_files[0].read_text(encoding='utf-8')
    else:
        print("⚠️  No JD file found. Please provide JD text.")
        print("   Expected location: data/jobs/jd.txt")
        jd_text = input("Please paste JD text (or press Enter to use sample): ").strip()
        if not jd_text:
            print("Using sample JD...")
            jd_text = """Senior Manager, AI Business Value Creation

We are seeking a Senior Manager to lead AI initiatives that drive business value. 
The ideal candidate will have 5+ years of experience in AI/ML program management, 
strong technical background in machine learning and data science, and proven ability 
to translate AI capabilities into quantifiable business outcomes.

Key Responsibilities:
- Lead cross-functional AI programs from conception to deployment
- Develop business cases and secure executive buy-in for AI initiatives
- Manage vendor relationships and technical partnerships
- Drive AI adoption across multiple business units
- Measure and report on AI ROI and business impact

Required Skills:
- AI/ML program management
- Cross-functional collaboration
- Business case development
- Stakeholder management
- Technical understanding of ML/AI systems"""
    
    # Load projects
    if project_files:
        print(f"📁 Found project file: {project_files[0].name}")
        project_materials = project_files[0].read_text(encoding='utf-8')
    else:
        print("⚠️  No project file found. Project materials are optional.")
        print("   Expected location: data/projects/projects.txt")
        project_materials = input("Please paste project materials (or press Enter to skip): ").strip()
        if not project_materials:
            print("No project materials provided. Continuing without projects...")
            project_materials = None
    
    return resume_text, jd_text, project_materials


def save_outputs(output_dir: Path, outputs: dict):
    """Save all outputs to files."""
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save Agent 1 output
    if "agent1_result" in outputs:
        with open(output_dir / f"agent1_validation_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(outputs["agent1_result"], f, indent=2, ensure_ascii=False)
    
    # Save Agent 2 output
    if "agent2_outputs" in outputs:
        with open(output_dir / f"agent2_analysis_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(outputs["agent2_outputs"], f, indent=2, ensure_ascii=False)
    
    # Save Agent 3 output
    if "agent3_outputs" in outputs:
        with open(output_dir / f"agent3_packaging_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(outputs["agent3_outputs"], f, indent=2, ensure_ascii=False)
    
    # Save Agent 4 output
    if "agent4_outputs" in outputs:
        with open(output_dir / f"agent4_optimization_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(outputs["agent4_outputs"], f, indent=2, ensure_ascii=False)
    
    # Save final resume
    if "final_resume" in outputs:
        with open(output_dir / f"final_resume_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(outputs["final_resume"])
    
    # Save Agent 5 output
    if "agent5_outputs" in outputs:
        with open(output_dir / f"agent5_interview_prep_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(outputs["agent5_outputs"], f, indent=2, ensure_ascii=False)
    
    # Save complete summary
    summary = {
        "timestamp": timestamp,
        "workflow_completed": True,
        "outputs": {
            "agent1": "agent1_validation_{timestamp}.json" if "agent1_result" in outputs else None,
            "agent2": "agent2_analysis_{timestamp}.json" if "agent2_outputs" in outputs else None,
            "agent3": "agent3_packaging_{timestamp}.json" if "agent3_outputs" in outputs else None,
            "agent4": "agent4_optimization_{timestamp}.json" if "agent4_outputs" in outputs else None,
            "final_resume": "final_resume_{timestamp}.txt" if "final_resume" in outputs else None,
            "agent5": "agent5_interview_prep_{timestamp}.json" if "agent5_outputs" in outputs else None
        }
    }
    
    with open(output_dir / f"complete_workflow_summary_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return timestamp


def main():
    """Run complete application workflow."""
    print("="*80)
    print("AI Job Hunting Assistant - Complete Application Run")
    print("="*80)
    print()
    
    # Load user data
    print("📥 Loading user data...")
    resume_text, jd_text, project_materials = load_user_data()
    print(f"   ✅ Resume loaded: {len(resume_text)} characters")
    print(f"   ✅ JD loaded: {len(jd_text)} characters")
    if project_materials:
        print(f"   ✅ Project materials loaded: {len(project_materials)} characters")
    else:
        print(f"   ⚠️  No project materials provided")
    print()
    
    # Step 1: Agent 1 - Validation
    print("="*80)
    print("STEP 1: Input Validation (Agent 1)")
    print("="*80)
    agent1 = InputValidationAgent()
    try:
        agent1_result = agent1.validate_inputs(resume_text, project_materials)
        print(f"✅ Validation result: {'PASSED' if agent1_result.get('is_valid') else 'FAILED'}")
        if not agent1_result.get('is_valid'):
            print(f"   Issues: {agent1_result.get('validation_summary', 'Unknown')}")
            print("   Please fix the issues and try again.")
            return
        print(f"   Summary: {agent1_result.get('validation_summary', 'Valid')}")
    except Exception as e:
        print(f"❌ Agent 1 failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    print()
    
    # Step 2: Agent 2 - JD Analysis
    print("="*80)
    print("STEP 2: JD Analysis & Matching Assessment (Agent 2)")
    print("="*80)
    agent2 = JDAnalysisAgent()
    try:
        print("🤖 Running Agent 2 analysis (this may take 30-60 seconds)...")
        agent2_outputs = agent2.analyze_jd_and_match(jd_text, resume_text, project_materials)
        
        if "error" in agent2_outputs:
            print(f"❌ Agent 2 error: {agent2_outputs['error']}")
            return
        
        match_score = agent2_outputs.get("match_assessment", {}).get("overall_match_score", "N/A")
        match_level = agent2_outputs.get("match_assessment", {}).get("match_level", "N/A")
        print(f"✅ Agent 2 analysis completed")
        print(f"   Match Score: {match_score} / 5.0")
        print(f"   Match Level: {match_level}")
    except Exception as e:
        print(f"❌ Agent 2 failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    print()
    
    # Step 3: Agent 3 - Project Packaging
    print("="*80)
    print("STEP 3: Project Packaging (Agent 3)")
    print("="*80)
    if not project_materials:
        print("⚠️  No project materials provided. Skipping Agent 3.")
        agent3_outputs = {"selected_projects": [], "skipped_projects": []}
    else:
        agent3 = ProjectPackagingAgent()
        try:
            print("🤖 Running Agent 3 packaging (this may take 30-60 seconds)...")
            agent3_outputs = agent3.package_projects(jd_text, project_materials, agent2_outputs)
            
            if "error" in agent3_outputs:
                print(f"⚠️  Agent 3 error: {agent3_outputs['error']}")
                agent3_outputs = {"selected_projects": [], "skipped_projects": []}
            else:
                selected_count = len(agent3_outputs.get("selected_projects", []))
                print(f"✅ Agent 3 packaging completed")
                print(f"   Selected projects: {selected_count}")
        except Exception as e:
            print(f"❌ Agent 3 failed: {str(e)}")
            import traceback
            traceback.print_exc()
            agent3_outputs = {"selected_projects": [], "skipped_projects": []}
    print()
    
    # Step 4: Agent 4 - Resume Optimization
    print("="*80)
    print("STEP 4: Resume Optimization (Agent 4)")
    print("="*80)
    agent4 = ResumeOptimizationAgent()
    service = ResumeOptimizationService()
    
    try:
        print("🤖 Running Agent 4 optimization (this may take 30-60 seconds)...")
        recommendations = agent4.optimize_resume(
            jd_text=jd_text,
            resume_text=resume_text,
            agent2_outputs=agent2_outputs,
            agent3_outputs=agent3_outputs
        )
        
        print(f"✅ Agent 4 optimization recommendations generated")
        replacement_count = len(recommendations.get("experience_replacements", []))
        adjustment_count = sum(
            len(adj.get("adjustments", []))
            for adj in recommendations.get("format_content_adjustments", [])
        )
        print(f"   Replacement recommendations: {replacement_count}")
        print(f"   Format adjustments: {adjustment_count}")
        
        # Load into service
        service.load_original_resume(resume_text)
        service.load_agent3_outputs(agent3_outputs)
        service.load_optimization_recommendations(recommendations)
        
        # Simulate user feedback (accept all replacements for demo)
        print("\n   📝 Simulating user feedback (accepting all replacements)...")
        for idx in range(replacement_count):
            service.submit_feedback(
                "experience_replacement",
                f"replacement_{idx}",
                "accept"
            )
        
        # Generate final resume
        final_result = service.apply_feedback_and_generate_resume()
        
        if "error" in final_result:
            print(f"❌ Error generating final resume: {final_result['error']}")
            return
        
        print(f"✅ Final resume generated")
        print(f"   Modifications applied: {final_result.get('total_modifications', 0)}")
        
        agent4_outputs = {
            "recommendations": recommendations,
            "final_resume": final_result["final_resume"],
            "classified_projects": final_result["classified_projects"]
        }
        
    except Exception as e:
        print(f"❌ Agent 4 failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    print()
    
    # Step 5: Agent 5 - Interview Preparation
    print("="*80)
    print("STEP 5: Interview Preparation (Agent 5)")
    print("="*80)
    agent5 = InterviewPreparationAgent()
    
    try:
        print("🤖 Running Agent 5 interview preparation (this may take 60-90 seconds)...")
        agent5_outputs = agent5.prepare_interview(
            jd_text=jd_text,
            final_resume=agent4_outputs["final_resume"],
            agent2_outputs=agent2_outputs,
            agent4_outputs=agent4_outputs
        )
        
        theme1 = agent5_outputs.get("theme_1_behavioral_interview", {})
        theme2 = agent5_outputs.get("theme_2_project_deep_dive", {})
        theme3 = agent5_outputs.get("theme_3_business_domain", {})
        
        print(f"✅ Agent 5 interview preparation completed")
        print(f"   Behavioral questions: {len(theme1.get('top_10_behavioral_questions', []))}")
        print(f"   Projects analyzed: {len(theme2.get('selected_projects', []))}")
        print(f"   Business questions: {len(theme3.get('business_questions', []))}")
        
    except Exception as e:
        print(f"❌ Agent 5 failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    print()
    
    # Save all outputs
    print("="*80)
    print("💾 Saving All Outputs")
    print("="*80)
    output_dir = Path(__file__).parent / "data" / "outputs"
    outputs = {
        "agent1_result": agent1_result,
        "agent2_outputs": agent2_outputs,
        "agent3_outputs": agent3_outputs,
        "agent4_outputs": agent4_outputs,
        "final_resume": agent4_outputs["final_resume"],
        "agent5_outputs": agent5_outputs
    }
    
    timestamp = save_outputs(output_dir, outputs)
    print(f"✅ All outputs saved to: data/outputs/")
    print(f"   Timestamp: {timestamp}")
    print()
    
    # Export final resume
    print("="*80)
    print("📄 Exporting Final Resume")
    print("="*80)
    exporter = ResumeExporter()
    try:
        pdf_path = output_dir / f"final_resume_{timestamp}.pdf"
        docx_path = output_dir / f"final_resume_{timestamp}.docx"
        
        exporter.export_to_pdf(agent4_outputs["final_resume"], str(pdf_path))
        print(f"✅ PDF exported: {pdf_path.name}")
        
        exporter.export_to_docx(agent4_outputs["final_resume"], str(docx_path))
        print(f"✅ DOCX exported: {docx_path.name}")
    except Exception as e:
        print(f"⚠️  Export error: {str(e)}")
    print()
    
    # Final Summary
    print("="*80)
    print("✅ COMPLETE APPLICATION RUN - SUCCESS!")
    print("="*80)
    print()
    print("📊 Summary:")
    print(f"  ✅ Agent 1: Input Validation - PASSED")
    print(f"  ✅ Agent 2: JD Analysis - Match Score: {match_score}/5.0")
    print(f"  ✅ Agent 3: Project Packaging - {len(agent3_outputs.get('selected_projects', []))} projects")
    print(f"  ✅ Agent 4: Resume Optimization - {final_result.get('total_modifications', 0)} modifications")
    print(f"  ✅ Agent 5: Interview Preparation - Complete")
    print()
    print("📁 Output Files:")
    print(f"  • Agent 2 Analysis: data/outputs/agent2_analysis_{timestamp}.json")
    print(f"  • Agent 3 Packaging: data/outputs/agent3_packaging_{timestamp}.json")
    print(f"  • Agent 4 Optimization: data/outputs/agent4_optimization_{timestamp}.json")
    print(f"  • Final Resume: data/outputs/final_resume_{timestamp}.txt")
    print(f"  • Final Resume PDF: data/outputs/final_resume_{timestamp}.pdf")
    print(f"  • Final Resume DOCX: data/outputs/final_resume_{timestamp}.docx")
    print(f"  • Agent 5 Interview Prep: data/outputs/agent5_interview_prep_{timestamp}.json")
    print()
    print("🎉 All outputs generated successfully!")
    print("="*80)


if __name__ == "__main__":
    main()
