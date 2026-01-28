/** Type definitions for the application */

export interface WorkflowState {
  workflow_id: string | null;
  status: 'idle' | 'running' | 'completed' | 'failed';
  current_step: string;
  progress: number;
  message: string;
  results: {
    agent1?: any;
    agent2?: any;
    agent3?: any;
    agent4?: any;
  };
  error: string | null;
}

export interface InterviewState {
  interview_id: string | null;
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  result: any;
  error: string | null;
}

export interface UserInputs {
  jd_text: string;
  resume_text: string;
  projects_text: string;
}

export interface FeedbackItem {
  feedback_type: 'experience_replacement' | 'format_adjustment' | 'experience_optimization' | 'skills_optimization';
  item_id: string;
  feedback: 'accept' | 'reject' | 'further_modify';
  additional_notes?: string;
  modified_text?: string;
}

export interface AppState {
  // User inputs
  inputs: UserInputs;
  
  // Workflow state
  workflow: WorkflowState;
  
  // Interview state
  interview: InterviewState;
  
  // Final resume
  final_resume: string | null;
  
  // Current page
  current_page: 'input' | 'dashboard' | 'interview';
  
  // Retry count
  retry_count: number;
}
