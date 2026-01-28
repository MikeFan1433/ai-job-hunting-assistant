"""Resume Optimization Service - Handles user feedback and generates final resume."""
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime


class ResumeOptimizationService:
    """Service to handle user feedback on resume optimization and generate final resume."""
    
    def __init__(self):
        """Initialize the resume optimization service."""
        self.original_resume = ""
        self.optimization_recommendations = {}
        self.user_feedback = {}
        self.final_resume = ""
        self.modification_history = []
        self.project_classification = {
            "resume_adopted_projects": [],
            "resume_not_adopted_projects": []
        }
        self.agent3_outputs = {}  # Store Agent 3 outputs for project classification
    
    def load_optimization_recommendations(self, recommendations: Dict) -> None:
        """
        Load optimization recommendations from Agent 4.
        
        Args:
            recommendations: Dictionary with optimization recommendations from Agent 4
        """
        self.optimization_recommendations = recommendations
        self.user_feedback = {
            "experience_replacements": {},
            "format_content_adjustments": {},
            "experience_optimizations": {},
            "skills_section_optimization": {}
        }
        
        # Extract project classification if available
        if "project_classification" in recommendations:
            self.project_classification = recommendations["project_classification"]
    
    def load_agent3_outputs(self, agent3_outputs: Dict) -> None:
        """
        Load Agent 3 outputs for project classification.
        
        Args:
            agent3_outputs: Complete Agent 3 output including selected_projects
        """
        self.agent3_outputs = agent3_outputs
    
    def load_original_resume(self, resume_text: str) -> None:
        """
        Load the original resume text.
        
        Args:
            resume_text: Original resume text
        """
        self.original_resume = resume_text
    
    def submit_feedback(
        self,
        feedback_type: str,  # "experience_replacement", "format_adjustment", "experience_optimization", or "skills_optimization"
        item_id: str,  # Unique identifier for the item
        feedback: str,  # "accept", "further_modify", or "reject"
        additional_notes: Optional[str] = None
    ) -> Dict:
        """
        Submit user feedback for a specific optimization recommendation.
        
        Args:
            feedback_type: Type of feedback ("experience_replacement" or "format_adjustment")
            item_id: Unique identifier for the recommendation item
            feedback: User's feedback choice ("accept", "further_modify", or "reject")
            additional_notes: Optional additional notes from user
        
        Returns:
            Dictionary with feedback confirmation and next steps
        """
        if feedback_type == "experience_replacement":
            if "experience_replacements" not in self.user_feedback:
                self.user_feedback["experience_replacements"] = {}
            
            self.user_feedback["experience_replacements"][item_id] = {
                "feedback": feedback,
                "additional_notes": additional_notes,
                "timestamp": datetime.now().isoformat()
            }
        
        elif feedback_type == "format_adjustment":
            if "format_content_adjustments" not in self.user_feedback:
                self.user_feedback["format_content_adjustments"] = {}
            
            self.user_feedback["format_content_adjustments"][item_id] = {
                "feedback": feedback,
                "additional_notes": additional_notes,
                "timestamp": datetime.now().isoformat()
            }
        
        elif feedback_type == "experience_optimization":
            if "experience_optimizations" not in self.user_feedback:
                self.user_feedback["experience_optimizations"] = {}
            
            self.user_feedback["experience_optimizations"][item_id] = {
                "feedback": feedback,
                "additional_notes": additional_notes,
                "timestamp": datetime.now().isoformat()
            }
        
        elif feedback_type == "skills_optimization":
            self.user_feedback["skills_section_optimization"] = {
                "feedback": feedback,
                "additional_notes": additional_notes,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "message": f"Feedback '{feedback}' recorded for {feedback_type} item {item_id}",
            "next_steps": self._get_next_steps(feedback_type, item_id, feedback)
        }
    
    def _get_next_steps(self, feedback_type: str, item_id: str, feedback: str) -> List[str]:
        """Get next steps based on user feedback."""
        if feedback == "accept":
            return ["The change will be applied to the final resume"]
        elif feedback == "further_modify":
            return ["Please provide additional modification instructions"]
        elif feedback == "reject":
            return ["The original content will be kept in the final resume"]
        return []
    
    def apply_feedback_and_generate_resume(self) -> Dict:
        """
        Apply all user feedback and generate the final optimized resume.
        After applying replacements, update project classification.
        
        Returns:
            Dictionary with final resume text, modification summary, and updated project classification
        """
        if not self.original_resume:
            return {
                "error": "Original resume not loaded",
                "final_resume": "",
                "modifications_applied": [],
                "project_classification": self.project_classification
            }
        
        if not self.optimization_recommendations:
            return {
                "error": "Optimization recommendations not loaded",
                "final_resume": self.original_resume,
                "modifications_applied": [],
                "project_classification": self.project_classification
            }
        
        final_resume = self.original_resume
        modifications_applied = []
        adopted_project_indices = []  # Track which projects were adopted
        
        # Apply experience replacements
        if "experience_replacements" in self.optimization_recommendations:
            for idx, replacement in enumerate(self.optimization_recommendations["experience_replacements"]):
                item_id = f"replacement_{idx}"
                feedback = self.user_feedback.get("experience_replacements", {}).get(item_id, {})
                
                if feedback.get("feedback") == "accept":
                    # Apply the replacement
                    result = self._apply_experience_replacement(
                        final_resume,
                        replacement,
                        feedback.get("additional_notes")
                    )
                    final_resume = result["updated_resume"]
                    modifications_applied.append(result["modification"])
                    
                    # Track which project was adopted
                    replacement_project = replacement.get("replacement_project", {})
                    project_index = replacement_project.get("project_index")
                    if project_index is not None:
                        adopted_project_indices.append(project_index)
        
        # Apply format/content adjustments
        if "format_content_adjustments" in self.optimization_recommendations:
            for adjustment_group in self.optimization_recommendations["format_content_adjustments"]:
                entry_id = self._get_entry_id(adjustment_group)
                
                for adj_idx, adjustment in enumerate(adjustment_group.get("adjustments", [])):
                    item_id = f"adjustment_{entry_id}_{adj_idx}"
                    feedback = self.user_feedback.get("format_content_adjustments", {}).get(item_id, {})
                    
                    if feedback.get("feedback") == "accept":
                        # Apply the adjustment
                        result = self._apply_format_adjustment(
                            final_resume,
                            adjustment_group,
                            adjustment,
                            feedback.get("additional_notes")
                        )
                        final_resume = result["updated_resume"]
                        modifications_applied.append(result["modification"])
        
        # Apply experience optimizations (Step 1.4)
        if "experience_optimizations" in self.optimization_recommendations:
            for opt_idx, optimization in enumerate(self.optimization_recommendations["experience_optimizations"]):
                entry = optimization.get("experience_entry", {})
                entry_id = f"{entry.get('title', '')}_{entry.get('company', '')}_{entry.get('entry_index', opt_idx)}"
                item_id = f"experience_opt_{entry_id}"
                feedback = self.user_feedback.get("experience_optimizations", {}).get(item_id, {})
                
                if feedback.get("feedback") == "accept":
                    # Apply the experience optimization
                    result = self._apply_experience_optimization(
                        final_resume,
                        optimization,
                        feedback.get("additional_notes")
                    )
                    final_resume = result["updated_resume"]
                    modifications_applied.append(result["modification"])
        
        # Apply skills section optimization
        if "skills_section_optimization" in self.optimization_recommendations:
            skills_opt = self.optimization_recommendations["skills_section_optimization"]
            feedback = self.user_feedback.get("skills_section_optimization", {})
            
            if feedback.get("feedback") == "accept" and skills_opt.get("has_skills_section", False):
                # Apply the skills section optimization
                result = self._apply_skills_optimization(
                    final_resume,
                    skills_opt,
                    feedback.get("additional_notes")
                )
                final_resume = result["updated_resume"]
                modifications_applied.append(result["modification"])
        
        self.final_resume = final_resume
        
        # Update project classification based on applied replacements
        updated_classification = self._update_project_classification(adopted_project_indices)
        
        # Get classified projects with full details for output
        classified_projects = self.get_classified_projects_for_interview()
        
        return {
            "final_resume": final_resume,  # 1. 最终优化后的简历
            "classified_projects": classified_projects,  # 2. 经过采纳分类后的项目文本（包含完整项目详情）
            "modifications_applied": modifications_applied,
            "total_modifications": len(modifications_applied),
            "summary": self._generate_modification_summary(modifications_applied),
            "project_classification": updated_classification  # 分类摘要（索引和名称）
        }
    
    def _apply_experience_replacement(
        self,
        resume: str,
        replacement: Dict,
        additional_notes: Optional[str] = None
    ) -> Dict:
        """
        Apply an experience replacement to the resume.
        
        Args:
            resume: Current resume text
            replacement: Replacement recommendation from Agent 4
            additional_notes: Optional additional notes from user
        
        Returns:
            Dictionary with updated resume and modification details
        """
        experience_to_replace = replacement.get("experience_to_replace", {})
        replacement_instructions = replacement.get("replacement_instructions", {})
        
        # Find the experience in the resume
        title = experience_to_replace.get("title", "")
        company = experience_to_replace.get("company", "")
        duration = experience_to_replace.get("duration", "")
        current_description = experience_to_replace.get("current_description", [])
        
        # Build search pattern to find the entire experience block
        # Look for title, company, duration, and description
        pattern_parts = []
        if title:
            pattern_parts.append(re.escape(title))
        if company:
            pattern_parts.append(re.escape(company))
        
        # Build the full experience block pattern
        experience_block_pattern = self._build_experience_block_pattern(
            title, company, duration, current_description
        )
        
        # Build replacement text
        # Use resume_experience_description if available, otherwise build from new_bullets
        resume_experience_desc = replacement_instructions.get("resume_experience_description", "")
        new_title = replacement_instructions.get("new_title", title)
        
        if resume_experience_desc:
            # Use the provided resume experience description
            if company and duration:
                header = f"{new_title} | {company} | {duration}"
            elif company:
                header = f"{new_title} | {company}"
            else:
                header = new_title
            
            replacement_text = f"{header}\n\n{resume_experience_desc}"
        else:
            # Fallback: build from new_bullets
            new_bullets = replacement_instructions.get("new_bullets", [])
            replacement_text = self._build_experience_text(
                new_title,
                company,
                duration,
                new_bullets
            )
        
        # Apply replacement
        if experience_block_pattern:
            updated_resume = re.sub(
                experience_block_pattern,
                replacement_text,
                resume,
                flags=re.DOTALL | re.MULTILINE
            )
        else:
            # Fallback: try simpler pattern
            if pattern_parts:
                simple_pattern = r"(" + "|".join(pattern_parts) + r")[^\n]*\n.*?(?=\n[A-Z]|\n\n|$)"
                updated_resume = re.sub(simple_pattern, replacement_text, resume, flags=re.DOTALL)
            else:
                # Last resort: append if not found
                updated_resume = resume + "\n\n" + replacement_text
        
        modification = {
            "type": "experience_replacement",
            "original": f"{title} at {company}",
            "replaced_with": new_title,
            "notes": additional_notes
        }
        
        return {
            "updated_resume": updated_resume,
            "modification": modification
        }
    
    def _apply_format_adjustment(
        self,
        resume: str,
        adjustment_group: Dict,
        adjustment: Dict,
        additional_notes: Optional[str] = None
    ) -> Dict:
        """
        Apply a format/content adjustment to the resume.
        
        Args:
            resume: Current resume text
            adjustment_group: Adjustment group from Agent 4
            adjustment: Specific adjustment to apply
            additional_notes: Optional additional notes from user
        
        Returns:
            Dictionary with updated resume and modification details
        """
        bullet_point = adjustment.get("bullet_point", {})
        original = bullet_point.get("original", "")
        suggested = bullet_point.get("suggested", "")
        
        if not original or not suggested:
            return {
                "updated_resume": resume,
                "modification": {
                    "type": "format_adjustment",
                    "status": "skipped",
                    "reason": "Missing original or suggested text"
                }
            }
        
        # Replace the original text with suggested text
        # Escape special regex characters
        original_escaped = re.escape(original)
        updated_resume = re.sub(original_escaped, suggested, resume, count=1)
        
        modification = {
            "type": "format_adjustment",
            "original": original,
            "suggested": suggested,
            "improvement_type": bullet_point.get("improvement_type", ""),
            "notes": additional_notes
        }
        
        return {
            "updated_resume": updated_resume,
            "modification": modification
        }
    
    def _apply_experience_optimization(
        self,
        resume: str,
        optimization: Dict,
        additional_notes: Optional[str] = None
    ) -> Dict:
        """
        Apply an experience optimization to the resume (Step 1.4).
        
        Args:
            resume: Current resume text
            optimization: Experience optimization recommendation from Agent 4
            additional_notes: Optional additional notes from user
        
        Returns:
            Dictionary with updated resume and modification details
        """
        experience_entry = optimization.get("experience_entry", {})
        optimized_experience = optimization.get("optimized_experience", {})
        
        # Find the experience in the resume
        title = experience_entry.get("title", "")
        company = experience_entry.get("company", "")
        duration = experience_entry.get("duration", "")
        
        # Build pattern to find the entire experience block
        experience_block_pattern = self._build_experience_block_pattern(
            title, company, duration, []
        )
        
        # Build optimized experience text
        optimized_title = optimized_experience.get("title", title)
        optimized_company = optimized_experience.get("company", company)
        optimized_duration = optimized_experience.get("duration", duration)
        optimized_bullets = optimized_experience.get("optimized_bullets", [])
        
        # Build replacement text
        replacement_text = self._build_experience_text(
            optimized_title,
            optimized_company,
            optimized_duration,
            optimized_bullets
        )
        
        # Apply replacement
        if experience_block_pattern:
            updated_resume = re.sub(
                experience_block_pattern,
                replacement_text,
                resume,
                flags=re.DOTALL | re.MULTILINE
            )
        else:
            # Fallback: try simpler pattern
            if title or company:
                simple_pattern = rf"({re.escape(title) if title else ''}.*?{re.escape(company) if company else ''})[^\n]*\n.*?(?=\n[A-Z]|\n\n|$)"
                updated_resume = re.sub(simple_pattern, replacement_text, resume, flags=re.DOTALL)
            else:
                updated_resume = resume
        
        modification = {
            "type": "experience_optimization",
            "original": f"{title} at {company}",
            "optimized": f"{optimized_title} at {optimized_company}",
            "bullets_optimized": len(optimized_bullets),
            "notes": additional_notes
        }
        
        return {
            "updated_resume": updated_resume,
            "modification": modification
        }
    
    def _apply_skills_optimization(
        self,
        resume: str,
        skills_optimization: Dict,
        additional_notes: Optional[str] = None
    ) -> Dict:
        """
        Apply skills section optimization to the resume.
        
        Args:
            resume: Current resume text
            skills_optimization: Skills optimization recommendation from Agent 4
            additional_notes: Optional additional notes from user
        
        Returns:
            Dictionary with updated resume and modification details
        """
        if not skills_optimization.get("has_skills_section", False):
            return {
                "updated_resume": resume,
                "modification": {
                    "type": "skills_optimization",
                    "status": "skipped",
                    "reason": "No skills section found in resume"
                }
            }
        
        current_skills = skills_optimization.get("current_skills", [])
        updated_resume = resume
        categories_optimized = 0
        
        # Find and replace each skill category
        for skill_category in current_skills:
            category_name = skill_category.get("skill_category", "")
            current_skills_list = skill_category.get("current_skills_list", [])
            optimized_skills_list = skill_category.get("optimized_skills_list", [])
            
            if not optimized_skills_list:
                continue
            
            # Try to find the skills section by category name or common section headers
            # Look for section header followed by skills
            section_pattern = rf"(?i)({re.escape(category_name)}|Skills|Technical Skills|Core Competencies|Proficiencies)[\s:]*\n?([^\n]*(?:\n[^\n]*)*?)(?=\n\n|\n[A-Z][A-Z\s]+\n|$)"
            section_match = re.search(section_pattern, updated_resume, re.MULTILINE)
            
            if section_match:
                section_header = section_match.group(1)
                section_content = section_match.group(2)
                
                # Determine format (comma-separated, bullet points, or line-separated)
                is_comma_separated = "," in section_content
                is_bullet_format = "•" in section_content or re.search(r"^[\s]*[-*]", section_content, re.MULTILINE)
                
                # Build optimized skills list as string
                if is_comma_separated:
                    optimized_skills_text = ", ".join(optimized_skills_list)
                elif is_bullet_format:
                    bullet_char = "•" if "•" in section_content else "-"
                    optimized_skills_text = "\n".join([f"{bullet_char} {skill}" for skill in optimized_skills_list])
                else:
                    optimized_skills_text = "\n".join(optimized_skills_list)
                
                # Replace the entire section content with optimized version
                replacement = f"{section_header}:\n{optimized_skills_text}"
                updated_resume = re.sub(
                    rf"{re.escape(section_match.group(0))}",
                    replacement,
                    updated_resume,
                    count=1
                )
                categories_optimized += 1
            else:
                # If section not found, try to append at the end of resume
                # This is a fallback - ideally the section should exist
                # Default to bullet format if section not found
                optimized_skills_text = "\n".join([f"• {skill}" for skill in optimized_skills_list])
                
                section_header = category_name if category_name else "Skills"
                new_section = f"\n\n{section_header}:\n{optimized_skills_text}"
                updated_resume = updated_resume + new_section
                categories_optimized += 1
        
        modification = {
            "type": "skills_optimization",
            "categories_optimized": categories_optimized,
            "notes": additional_notes
        }
        
        return {
            "updated_resume": updated_resume,
            "modification": modification
        }
    
    def _build_experience_block_pattern(
        self,
        title: str,
        company: str,
        duration: str,
        description: List[str]
    ) -> Optional[str]:
        """Build regex pattern to find entire experience block in resume."""
        if not title and not company:
            return None
        
        # Build pattern for the header line (title | company | duration)
        header_pattern = ""
        if title and company:
            if duration:
                header_pattern = rf"{re.escape(title)}\s*\|\s*{re.escape(company)}\s*\|\s*{re.escape(duration)}"
            else:
                header_pattern = rf"{re.escape(title)}\s*\|\s*{re.escape(company)}"
        elif title:
            header_pattern = re.escape(title)
        elif company:
            header_pattern = re.escape(company)
        
        if not header_pattern:
            return None
        
        # Build pattern for description bullets
        bullet_pattern = ""
        if description:
            # Match any bullets after the header until next section
            bullet_pattern = r"(?:\n\s*[•\-\*]\s*[^\n]*)*"
        
        # Match until next section (all caps header or double newline)
        full_pattern = rf"{header_pattern}.*?{bullet_pattern}(?=\n\n|\n[A-Z][A-Z\s]+\n|$)"
        
        return full_pattern
    
    def _build_experience_search_pattern(
        self,
        title: str,
        company: str,
        description: List[str]
    ) -> Optional[str]:
        """Build regex pattern to find experience in resume (legacy method)."""
        return self._build_experience_block_pattern(title, company, "", description)
    
    def _build_experience_text(
        self,
        title: str,
        company: str,
        duration: str,
        bullets: List[str]
    ) -> str:
        """Build formatted experience text for resume."""
        lines = []
        
        if title and company:
            if duration:
                lines.append(f"{title} | {company} | {duration}")
            else:
                lines.append(f"{title} | {company}")
        elif title:
            lines.append(title)
        
        lines.append("")  # Empty line
        
        for bullet in bullets:
            # Remove leading bullet symbols if present
            bullet = bullet.lstrip("•-* ").strip()
            lines.append(f"• {bullet}")
        
        return "\n".join(lines)
    
    def _update_project_classification(self, adopted_project_indices: List[int]) -> Dict:
        """
        Update project classification based on applied replacements.
        
        Args:
            adopted_project_indices: List of project indices that were adopted for resume
        
        Returns:
            Updated project classification dictionary
        """
        # Initialize classification if not exists
        if not self.project_classification:
            self.project_classification = {
                "resume_adopted_projects": [],
                "resume_not_adopted_projects": []
            }
        
        # Get all projects from Agent 3 outputs
        all_projects = []
        if self.agent3_outputs and "selected_projects" in self.agent3_outputs:
            all_projects = self.agent3_outputs["selected_projects"]
        
        # Reclassify projects
        resume_adopted = []
        resume_not_adopted = []
        
        for idx, project in enumerate(all_projects):
            project_info = {
                "project_index": idx,
                "project_name": project.get("project_name", f"Project {idx}"),
                "resume_adopted": idx in adopted_project_indices,
                "note": ""
            }
            
            if idx in adopted_project_indices:
                # Find which replacement uses this project
                replacement_idx = adopted_project_indices.index(idx)
                project_info["replacement_experience_index"] = replacement_idx
                project_info["note"] = "This project has been converted to resume experience and used in resume"
                resume_adopted.append(project_info)
            else:
                project_info["note"] = "This project will be kept in full detail for interview preparation"
                resume_not_adopted.append(project_info)
        
        updated_classification = {
            "resume_adopted_projects": resume_adopted,
            "resume_not_adopted_projects": resume_not_adopted
        }
        
        self.project_classification = updated_classification
        return updated_classification
    
    def convert_project_to_resume_experience(
        self,
        project: Dict,
        replacement_instructions: Dict
    ) -> str:
        """
        Convert optimized project text to resume experience description.
        
        Args:
            project: Optimized project from Agent 3
            replacement_instructions: Replacement instructions from Agent 4
        
        Returns:
            Formatted resume experience text
        """
        # Use the new_bullets from replacement_instructions if available
        new_bullets = replacement_instructions.get("new_bullets", [])
        
        # If new_bullets not available, extract from project
        if not new_bullets:
            optimized_version = project.get("optimized_version", {})
            summary_bullets = optimized_version.get("summary_bullets", [])
            if summary_bullets:
                new_bullets = summary_bullets
        
        # If still no bullets, extract from project framework
        if not new_bullets:
            rewritten = project.get("rewritten_with_gaps", {})
            results = rewritten.get("results_metrics", {})
            primary_metric = results.get("primary_metric", "")
            if primary_metric:
                new_bullets = [f"Achieved {primary_metric}"]
        
        # Build experience text
        new_title = replacement_instructions.get("new_title", project.get("project_name", ""))
        duration = ""  # Duration should be inferred or provided separately
        
        return self._build_experience_text(new_title, "", duration, new_bullets)
    
    def get_project_classification(self) -> Dict:
        """
        Get current project classification.
        
        Returns:
            Dictionary with project classification
        """
        return self.project_classification
    
    def get_classified_projects_for_interview(self) -> Dict:
        """
        Get classified projects organized for interview preparation.
        
        Returns:
            Dictionary with resume_adopted and resume_not_adopted projects with full details
        """
        result = {
            "resume_adopted_projects": [],
            "resume_not_adopted_projects": []
        }
        
        if not self.agent3_outputs or "selected_projects" not in self.agent3_outputs:
            return result
        
        all_projects = self.agent3_outputs["selected_projects"]
        adopted_indices = [
            p.get("project_index") 
            for p in self.project_classification.get("resume_adopted_projects", [])
        ]
        
        for idx, project in enumerate(all_projects):
            project_with_classification = {
                **project,
                "resume_adopted": idx in adopted_indices,
                "project_index": idx
            }
            
            if idx in adopted_indices:
                result["resume_adopted_projects"].append(project_with_classification)
            else:
                result["resume_not_adopted_projects"].append(project_with_classification)
        
        return result
    
    def _get_entry_id(self, adjustment_group: Dict) -> str:
        """Get unique identifier for an adjustment group."""
        entry = adjustment_group.get("experience_entry", {})
        title = entry.get("title", "")
        company = entry.get("company", "")
        entry_index = entry.get("entry_index", 0)
        
        return f"{title}_{company}_{entry_index}"
    
    def _generate_modification_summary(self, modifications: List[Dict]) -> Dict:
        """Generate summary of all modifications applied."""
        summary = {
            "total_modifications": len(modifications),
            "experience_replacements": 0,
            "format_adjustments": 0,
            "by_type": {}
        }
        
        for mod in modifications:
            mod_type = mod.get("type", "unknown")
            summary["by_type"][mod_type] = summary["by_type"].get(mod_type, 0) + 1
            
            if mod_type == "experience_replacement":
                summary["experience_replacements"] += 1
            elif mod_type == "format_adjustment":
                summary["format_adjustments"] += 1
        
        return summary
    
    def get_feedback_status(self) -> Dict:
        """
        Get current status of user feedback.
        
        Returns:
            Dictionary with feedback status
        """
        total_recommendations = 0
        feedback_received = 0
        
        # Count experience replacements
        if "experience_replacements" in self.optimization_recommendations:
            total_recommendations += len(self.optimization_recommendations["experience_replacements"])
            feedback_received += len(self.user_feedback.get("experience_replacements", {}))
        
        # Count format adjustments
        if "format_content_adjustments" in self.optimization_recommendations:
            for adjustment_group in self.optimization_recommendations["format_content_adjustments"]:
                adjustments = adjustment_group.get("adjustments", [])
                total_recommendations += len(adjustments)
                entry_id = self._get_entry_id(adjustment_group)
                for adj_idx in range(len(adjustments)):
                    item_id = f"adjustment_{entry_id}_{adj_idx}"
                    if item_id in self.user_feedback.get("format_content_adjustments", {}):
                        feedback_received += 1
        
        # Count experience optimizations
        if "experience_optimizations" in self.optimization_recommendations:
            total_recommendations += len(self.optimization_recommendations["experience_optimizations"])
            feedback_received += len(self.user_feedback.get("experience_optimizations", {}))
        
        # Count skills optimization
        if "skills_section_optimization" in self.optimization_recommendations:
            skills_opt = self.optimization_recommendations["skills_section_optimization"]
            if skills_opt.get("has_skills_section", False):
                total_recommendations += 1
                if "skills_section_optimization" in self.user_feedback:
                    feedback_received += 1
        
        return {
            "total_recommendations": total_recommendations,
            "feedback_received": feedback_received,
            "pending_feedback": total_recommendations - feedback_received,
            "completion_percentage": (feedback_received / total_recommendations * 100) if total_recommendations > 0 else 0
        }
    
    def save_final_resume(self, filepath: str, format: str = "txt") -> Dict:
        """
        Save final resume to file.
        
        Args:
            filepath: Path to save the file
            format: File format ("txt", "md", "json")
        
        Returns:
            Dictionary with save status
        """
        if not self.final_resume:
            return {
                "error": "Final resume not generated. Please call apply_feedback_and_generate_resume() first."
            }
        
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "txt" or format == "md":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.final_resume)
            elif format == "json":
                data = {
                    "final_resume": self.final_resume,
                    "modifications_applied": self.modification_history,
                    "generated_at": datetime.now().isoformat()
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                return {"error": f"Unsupported format: {format}"}
            
            return {
                "status": "success",
                "filepath": str(path),
                "format": format
            }
        except Exception as e:
            return {
                "error": f"Failed to save file: {str(e)}"
            }
