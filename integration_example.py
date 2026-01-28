"""Complete integration example for Resume Optimization Service."""
import json
from resume_optimization_service import ResumeOptimizationService
from resume_export import ResumeExporter
from agent4 import ResumeOptimizationAgent


def example_complete_workflow():
    """Example of complete workflow from optimization to export."""
    
    print("=" * 60)
    print("Complete Resume Optimization Workflow Example")
    print("=" * 60)
    
    # Step 1: Initialize services
    print("\n1. Initializing services...")
    service = ResumeOptimizationService()
    exporter = ResumeExporter()
    agent4 = ResumeOptimizationAgent()
    
    # Step 2: Load original resume
    print("2. Loading original resume...")
    original_resume = """JOHN DOE
Email: john.doe@email.com | Phone: (555) 123-4567

WORK EXPERIENCE

Software Engineer | Tech Corp | 2020-2022
• Developed web applications using Python and React
• Worked with team on various projects
• Implemented new features and fixed bugs

Data Scientist | Data Inc | 2018-2020
• Worked on AI projects and helped improve customer experience
• Analyzed data and created machine learning models
• Presented findings to stakeholders

EDUCATION

Master of Science in Computer Science | University of Technology | 2018
"""
    
    service.load_original_resume(original_resume)
    
    # Step 3: Simulate Agent 4 optimization recommendations
    print("3. Getting optimization recommendations from Agent 4...")
    # In real scenario, you would call:
    # recommendations = agent4.optimize_resume(jd_text, resume_text, agent2_outputs, agent3_outputs)
    
    # For this example, we'll use sample recommendations
    sample_recommendations = {
        "experience_replacements": [
            {
                "experience_to_replace": {
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "duration": "2020-2022",
                    "current_description": [
                        "Developed web applications using Python and React",
                        "Worked with team on various projects",
                        "Implemented new features and fixed bugs"
                    ]
                },
                "replacement_project": {
                    "project_name": "AI Chatbot System",
                    "optimized_text": "Full optimized project text...",
                    "key_highlights": [
                        "Led development of AI chatbot using RAG",
                        "Improved customer satisfaction by 30%",
                        "Managed cross-functional team of 5"
                    ]
                },
                "replacement_rationale": {
                    "why_replace": "Low relevance to JD requirements",
                    "why_better": "Better alignment with AI program management role",
                    "expected_improvement": "Will improve match score from 2.5 to 4.0"
                },
                "replacement_instructions": {
                    "new_title": "AI Program Manager",
                    "new_bullets": [
                        "Led cross-functional AI initiative to develop chatbot system using RAG technology",
                        "Improved customer satisfaction scores by 30% through AI-powered solutions",
                        "Managed team of 5 engineers and coordinated with product, engineering, and design teams"
                    ],
                    "jd_keywords_to_emphasize": ["AI", "cross-functional", "RAG", "program management"],
                    "formatting_notes": "Ensure consistent formatting"
                }
            }
        ],
        "format_content_adjustments": [
            {
                "experience_entry": {
                    "title": "Data Scientist",
                    "company": "Data Inc",
                    "entry_index": 0
                },
                "adjustments": [
                    {
                        "bullet_point": {
                            "original": "Worked on AI projects and helped improve customer experience",
                            "suggested": "Led cross-functional AI initiatives to enhance customer experience, resulting in 25% improvement in customer satisfaction scores",
                            "improvement_type": "Sentence structure enhancement + Metric addition + Keyword optimization",
                            "improvement_rationale": "Original is vague. Suggested version uses strong action verb, adds JD keywords, and includes quantifiable metric",
                            "jd_keywords_added": ["cross-functional", "AI initiatives", "customer experience"],
                            "expected_impact": "Improves skills match by demonstrating leadership and quantifiable impact"
                        },
                        "user_feedback_options": {
                            "accept": "Apply this change",
                            "further_modify": "I want additional adjustments",
                            "reject": "Keep original text"
                        }
                    }
                ]
            }
        ],
        "optimization_summary": {
            "total_experiences_analyzed": 2,
            "experiences_recommended_for_replacement": 1,
            "total_adjustments_suggested": 1,
            "expected_match_score_improvement": "1.5 points",
            "key_improvements": [
                "Added AI program management experience",
                "Enhanced bullet points with metrics and keywords"
            ]
        }
    }
    
    service.load_optimization_recommendations(sample_recommendations)
    
    # Step 4: Display recommendations to user (simulated)
    print("4. Displaying recommendations to user...")
    print(f"   - {len(sample_recommendations['experience_replacements'])} experience replacement(s)")
    print(f"   - {len(sample_recommendations['format_content_adjustments'])} format adjustment group(s)")
    
    # Step 5: User submits feedback
    print("\n5. User submitting feedback...")
    
    # Accept experience replacement
    feedback1 = service.submit_feedback(
        feedback_type="experience_replacement",
        item_id="replacement_0",
        feedback="accept",
        additional_notes="This replacement aligns well with the JD"
    )
    print(f"   ✓ Feedback 1: {feedback1['message']}")
    
    # Accept format adjustment
    feedback2 = service.submit_feedback(
        feedback_type="format_adjustment",
        item_id="adjustment_Data Scientist_Data Inc_0_0",
        feedback="accept",
        additional_notes="Good improvement with metrics"
    )
    print(f"   ✓ Feedback 2: {feedback2['message']}")
    
    # Check feedback status
    status = service.get_feedback_status()
    print(f"\n   Feedback Status: {status['feedback_received']}/{status['total_recommendations']} completed ({status['completion_percentage']:.1f}%)")
    
    # Step 6: Generate final resume
    print("\n6. Generating final optimized resume...")
    result = service.apply_feedback_and_generate_resume()
    
    if "error" in result:
        print(f"   ❌ Error: {result['error']}")
        return
    
    print(f"   ✓ Applied {result['total_modifications']} modifications")
    print(f"   - Experience replacements: {result['summary']['experience_replacements']}")
    print(f"   - Format adjustments: {result['summary']['format_adjustments']}")
    
    final_resume = result["final_resume"]
    
    # Step 7: Export to PDF and Word
    print("\n7. Exporting resume to PDF and Word...")
    
    # Export PDF
    pdf_result = exporter.export_to_pdf(
        resume_text=final_resume,
        output_path="data/resumes/john_doe_resume.pdf",
        title="John Doe - Resume"
    )
    if "error" in pdf_result:
        print(f"   ⚠ PDF Export: {pdf_result['error']}")
    else:
        print(f"   ✓ PDF exported: {pdf_result['filepath']} ({pdf_result['size_kb']} KB)")
    
    # Export Word
    docx_result = exporter.export_to_docx(
        resume_text=final_resume,
        output_path="data/resumes/john_doe_resume.docx",
        title="John Doe - Resume"
    )
    if "error" in docx_result:
        print(f"   ⚠ DOCX Export: {docx_result['error']}")
    else:
        print(f"   ✓ DOCX exported: {docx_result['filepath']} ({docx_result['size_kb']} KB)")
    
    # Step 8: Display final resume preview
    print("\n8. Final Resume Preview:")
    print("-" * 60)
    print(final_resume[:800] + "..." if len(final_resume) > 800 else final_resume)
    print("-" * 60)
    
    print("\n" + "=" * 60)
    print("✅ Complete workflow finished successfully!")
    print("=" * 60)
    
    return {
        "original_resume": original_resume,
        "final_resume": final_resume,
        "modifications": result["modifications_applied"],
        "pdf_path": pdf_result.get("filepath"),
        "docx_path": docx_result.get("filepath")
    }


if __name__ == "__main__":
    example_complete_workflow()
