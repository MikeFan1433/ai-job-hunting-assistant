"""Display complete test results in a readable format."""
import json
from pathlib import Path
from datetime import datetime

def print_section(title, char="=", width=100):
    """Print a formatted section header."""
    print("\n" + char * width)
    print(f"  {title}")
    print(char * width + "\n")


def load_latest_output(output_dir, prefix):
    """Load the latest output file with given prefix."""
    output_dir = Path(output_dir)
    if not output_dir.exists():
        return None
    
    files = sorted(output_dir.glob(f"{prefix}_*.json"), reverse=True)
    if not files:
        return None
    
    with open(files[0], "r", encoding="utf-8") as f:
        return json.load(f)


def display_agent1_output(output):
    """Display Agent 1 output."""
    print_section("AGENT 1: Input Validation Results", "-")
    
    if "error" in output:
        print(f"❌ Error: {output['error']}")
        return
    
    print(f"Validation Status: {output.get('validation_status', 'Unknown')}")
    print(f"Is Valid: {output.get('is_valid', False)}")
    
    if "issues" in output and output["issues"]:
        print(f"\nIssues Found: {len(output['issues'])}")
        for issue in output["issues"][:5]:  # Show first 5
            print(f"  - {issue.get('type', 'Unknown')}: {issue.get('description', '')}")
    else:
        print("✅ No issues found")


def display_agent2_output(output):
    """Display Agent 2 output."""
    print_section("AGENT 2: JD Analysis Results", "-")
    
    if "error" in output:
        print(f"❌ Error: {output['error']}")
        return
    
    # Match Assessment
    if "match_assessment" in output:
        match = output["match_assessment"]
        print("📊 Match Assessment:")
        print(f"   Overall Match Score: {match.get('overall_match_score', 'N/A')}")
        print(f"   Experience Match: {match.get('experience_match_score', 'N/A')}")
        print(f"   Skills Match: {match.get('skills_match_score', 'N/A')}")
        print(f"   Education Match: {match.get('education_match_score', 'N/A')}")
        
        if "strengths" in match:
            print(f"\n   Strengths ({len(match['strengths'])}):")
            for strength in match["strengths"][:3]:
                print(f"     • {strength}")
        
        if "gaps" in match:
            print(f"\n   Gaps ({len(match['gaps'])}):")
            for gap in match["gaps"][:3]:
                print(f"     • {gap}")
    
    # Ideal Candidate Profile
    if "ideal_candidate_profile" in output:
        profile = output["ideal_candidate_profile"]
        print("\n👤 Ideal Candidate Profile:")
        if "required_experience" in profile:
            print(f"   Required Experience: {profile['required_experience']}")
        if "required_skills" in profile:
            skills = profile["required_skills"][:5] if isinstance(profile["required_skills"], list) else []
            print(f"   Key Skills: {', '.join(skills)}")


def display_agent3_output(output):
    """Display Agent 3 output."""
    print_section("AGENT 3: Project Packaging Results", "-")
    
    if "error" in output:
        print(f"❌ Error: {output['error']}")
        return
    
    if "selected_projects" in output:
        print(f"✅ Selected Projects: {len(output['selected_projects'])}")
        for idx, project in enumerate(output["selected_projects"], 1):
            print(f"\n   Project {idx}: {project.get('project_name', 'Unknown')}")
            if "relevance_reason" in project:
                print(f"   Relevance: {project['relevance_reason'][:100]}...")
            
            if "optimized_version" in project:
                opt = project["optimized_version"]
                if "summary_bullets" in opt:
                    print(f"   Summary Bullets: {len(opt['summary_bullets'])}")
                    for bullet in opt["summary_bullets"][:2]:
                        print(f"     • {bullet[:80]}...")


def display_agent4_output(output):
    """Display Agent 4 output."""
    print_section("AGENT 4: Resume Optimization Results", "-")
    
    if "error" in output:
        print(f"❌ Error: {output['error']}")
        return
    
    print(f"Experience Replacements: {len(output.get('experience_replacements', []))}")
    print(f"Experience Optimizations: {len(output.get('experience_optimizations', []))}")
    print(f"Format Adjustments: {len(output.get('format_content_adjustments', []))}")
    
    skills_opt = output.get("skills_section_optimization", {})
    if skills_opt.get("has_skills_section", False):
        print(f"Skills Section Optimization: ✅ Yes")
        if "current_skills" in skills_opt:
            print(f"   Skill Categories: {len(skills_opt['current_skills'])}")
    else:
        print("Skills Section Optimization: No skills section found")
    
    # Show optimization summary
    if "optimization_summary" in output:
        summary = output["optimization_summary"]
        print(f"\n📊 Optimization Summary:")
        print(f"   Total Experiences Analyzed: {summary.get('total_experiences_analyzed', 0)}")
        print(f"   Experiences Recommended for Replacement: {summary.get('experiences_recommended_for_replacement', 0)}")
        print(f"   Total Adjustments Suggested: {summary.get('total_adjustments_suggested', 0)}")
        print(f"   Total Experiences Optimized: {summary.get('total_experiences_optimized', 0)}")
        print(f"   Expected Match Score Improvement: {summary.get('expected_match_score_improvement', 'N/A')}")


def display_final_resume(output):
    """Display final resume information."""
    print_section("FINAL OPTIMIZED RESUME", "-")
    
    if "error" in output:
        print(f"❌ Error: {output['error']}")
        return
    
    print(f"✅ Final Resume Generated")
    print(f"   Total Modifications Applied: {output.get('total_modifications', 0)}")
    
    if "modifications_applied" in output:
        mods = output["modifications_applied"]
        print(f"\n   Modifications:")
        for mod in mods[:5]:
            mod_type = mod.get("type", "unknown")
            print(f"     • {mod_type}: {mod.get('original', 'N/A')[:50]}...")
    
    # Show first 500 chars of final resume
    if "final_resume" in output:
        resume = output["final_resume"]
        print(f"\n   Resume Preview (first 500 chars):")
        print("   " + "-" * 80)
        print("   " + resume[:500].replace("\n", "\n   "))
        print("   " + "-" * 80)


def display_agent5_output(output):
    """Display Agent 5 output."""
    print_section("AGENT 5: Interview Preparation Results", "-")
    
    if "error" in output:
        print(f"❌ Error: {output['error']}")
        return
    
    # Theme 1: Behavioral Interview
    if "theme_1_behavioral_interview" in output:
        theme1 = output["theme_1_behavioral_interview"]
        print("✅ Theme 1: Behavioral Interview")
        
        if "self_introduction" in theme1:
            print("   • Self-Introduction: ✅ Generated")
        
        if "storytelling_example" in theme1:
            print("   • Storytelling Example: ✅ Generated")
        
        if "top_10_behavioral_questions" in theme1:
            questions = theme1["top_10_behavioral_questions"]
            print(f"   • Top 10 Behavioral Questions: {len(questions)} questions")
            for idx, q in enumerate(questions[:3], 1):
                print(f"     {idx}. {q.get('question', 'N/A')[:60]}...")
    
    # Theme 2: Project Deep-Dive
    if "theme_2_project_deep_dive" in output:
        theme2 = output["theme_2_project_deep_dive"]
        projects = theme2.get("selected_projects", [])
        print(f"\n✅ Theme 2: Project Deep-Dive")
        print(f"   Selected Projects: {len(projects)}")
        for idx, project in enumerate(projects[:3], 1):
            print(f"     {idx}. {project.get('project_name', 'Unknown')}")
            questions = project.get("technical_deep_dive_questions", [])
            print(f"        Technical Questions: {len(questions)}")
    
    # Theme 3: Business Domain
    if "theme_3_business_domain" in output:
        theme3 = output["theme_3_business_domain"]
        questions = theme3.get("business_questions", [])
        print(f"\n✅ Theme 3: Business Domain Questions")
        print(f"   Total Questions: {len(questions)}")
        for idx, q in enumerate(questions[:3], 1):
            print(f"     {idx}. {q.get('question', 'N/A')[:60]}...")


def main():
    """Display all test results."""
    output_dir = Path("data/outputs/complete_test")
    
    print_section("📊 COMPLETE APPLICATION TEST RESULTS", "=", 100)
    print(f"Results Directory: {output_dir}")
    print(f"Display Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load and display each agent's output
    agent1_output = load_latest_output(output_dir, "agent1")
    if agent1_output:
        display_agent1_output(agent1_output)
    
    agent2_output = load_latest_output(output_dir, "agent2")
    if agent2_output:
        display_agent2_output(agent2_output)
    
    agent3_output = load_latest_output(output_dir, "agent3")
    if agent3_output:
        display_agent3_output(agent3_output)
    
    agent4_output = load_latest_output(output_dir, "agent4")
    if agent4_output:
        display_agent4_output(agent4_output)
    
    final_resume_output = load_latest_output(output_dir, "final_resume")
    if final_resume_output:
        display_final_resume(final_resume_output)
    
    agent5_output = load_latest_output(output_dir, "agent5")
    if agent5_output:
        display_agent5_output(agent5_output)
    else:
        print_section("AGENT 5: Interview Preparation Results", "-")
        print("⚠️  Agent 5 output not found or failed to generate")
        print("   This may be due to JSON parsing issues with the LLM response")
    
    # Load complete output if available
    complete_output_files = sorted(output_dir.glob("complete_output_*.json"), reverse=True)
    if complete_output_files:
        print_section("📁 Complete Output File", "-")
        print(f"✅ Complete output saved to: {complete_output_files[0]}")
        print(f"   File size: {complete_output_files[0].stat().st_size / 1024:.2f} KB")
    
    print_section("✅ RESULTS DISPLAY COMPLETE", "=", 100)


if __name__ == "__main__":
    main()
