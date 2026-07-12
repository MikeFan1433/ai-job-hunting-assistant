/** API service for backend communication - Simplified and Reliable Version */
import axios from 'axios';

// Auto-detect API base URL
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  const origin = window.location.origin;
  
  // Check environment variable
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // Production domains
  if (hostname.includes('ai-builders.space')) {
    return origin;
  }
  
  // Development mode: use Vite proxy (empty string = same origin)
  if (import.meta.env.DEV || import.meta.env.MODE === 'development') {
    return '';
  }
  
  // Default: same origin
  return origin;
};

const api = axios.create({
  baseURL: getApiBaseUrl() || window.location.origin,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

/** Extract backend error detail from axios error (string or FastAPI validation array). */
export function extractApiErrorMessage(error: unknown, fallback = 'Request failed'): string {
  const err = error as { response?: { data?: { detail?: unknown } }; message?: string };
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'object' && d && 'msg' in d ? String((d as { msg: string }).msg) : String(d))).join('; ');
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail);
  return err.message || fallback;
}

// Health check API
export const healthAPI = {
  check: async (): Promise<boolean> => {
    try {
      const response = await api.get('/api/v1/health', { timeout: 3000 });
      return response.data?.status === 'healthy';
    } catch {
      return false;
    }
  },
};

// Resume API
export const resumeAPI = {
  uploadPDF: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/v1/upload/resume-pdf', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getRecommendations: async (workflowId?: string | null) => {
    const params = workflowId ? { workflow_id: workflowId } : undefined;
    const response = await api.get('/api/v1/resume/recommendations', { params });
    return response.data;
  },
  getFeedbackStatus: async () => {
    const response = await api.get('/api/v1/resume/feedback/status');
    return response.data;
  },
  submitFeedback: async (feedback: {
    feedback_type: string;
    item_id: string;
    feedback: string;
    modified_text?: string;
    additional_notes?: string;
    workflow_id?: string | null;
  }) => {
    const response = await api.post('/api/v1/resume/feedback', feedback);
    return response.data;
  },
  regenerateSuggestion: async (params: {
    workflow_id: string;
    feedback_type: string;
    item_id: string;
    user_instruction: string;
  }) => {
    const response = await api.post('/api/v1/resume/regenerate-suggestion', params);
    return response.data;
  },
  submitBatchFeedback: async (feedbacks: any[], workflowId?: string | null) => {
    const response = await api.post('/api/v1/resume/feedback/batch', {
      feedbacks,
      workflow_id: workflowId || undefined,
    });
    return response.data;
  },
  generateFinal: async (workflowId?: string | null) => {
    const response = await api.post(
      '/api/v1/resume/generate',
      { workflow_id: workflowId || undefined },
      { timeout: 180000 },
    );
    return response.data;
  },
  export: async (format: 'pdf' | 'docx', title: string, workflowId?: string | null) => {
    try {
      // #region agent log
      fetch('http://127.0.0.1:7589/ingest/6c0eeebb-9460-4871-89ae-8e5257503ace',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e8b8c3'},body:JSON.stringify({sessionId:'e8b8c3',location:'api.ts:export',message:'resume export request',data:{format,title,workflowId:workflowId||null},timestamp:Date.now(),hypothesisId:'PDF-FE'})}).catch(()=>{});
      // #endregion
      const response = await api.post('/api/v1/resume/export', {
        format,
        title,
        workflow_id: workflowId || undefined,
      }, {
        responseType: 'blob',
        timeout: 120000,
      });
      // #region agent log
      fetch('http://127.0.0.1:7589/ingest/6c0eeebb-9460-4871-89ae-8e5257503ace',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e8b8c3'},body:JSON.stringify({sessionId:'e8b8c3',location:'api.ts:export',message:'resume export response',data:{blobSize:response.data?.size||0,contentType:response.headers?.['content-type']||null},timestamp:Date.now(),hypothesisId:'PDF-FE'})}).catch(()=>{});
      // #endregion
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${title}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      return response.data;
    } catch (e: any) {
      const data = e.response?.data;
      if (data instanceof Blob) {
        const text = await data.text();
        try {
          const j = JSON.parse(text);
          const d = j.detail;
          throw new Error(typeof d === 'string' ? d : JSON.stringify(j));
        } catch (parseErr: unknown) {
          if (parseErr instanceof SyntaxError) {
            throw new Error(text.slice(0, 300) || e.message);
          }
          throw parseErr;
        }
      }
      throw e;
    }
  },
  exportProjects: async (format: 'pdf' | 'docx') => {
    const response = await api.post('/api/v1/export/projects', { format }, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Project_Materials.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
  exportInterview: async (interviewId: string, format: 'pdf' | 'docx') => {
    const response = await api.post('/api/v1/export/interview', { interview_id: interviewId, format }, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Interview_Prep.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
  /** Full interview prep as PDF from client-built plain text (all sections expanded). */
  exportInterviewPrepFullPdf: async (text: string, title: string) => {
    try {
      const response = await api.post(
        '/api/v1/export/text-document',
        { title, text, format: 'pdf' },
        { responseType: 'blob', timeout: 180000 }
      );
      const safe = title.replace(/[^\w\-.]+/g, '_').slice(0, 80) || 'Interview_Prep';
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${safe}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      return response.data;
    } catch (e: any) {
      const data = e.response?.data;
      if (data instanceof Blob) {
        const t = await data.text();
        try {
          const j = JSON.parse(t);
          const d = j.detail;
          throw new Error(typeof d === 'string' ? d : JSON.stringify(j));
        } catch (parseErr: unknown) {
          if (parseErr instanceof SyntaxError) {
            throw new Error(t.slice(0, 300) || e.message);
          }
          throw parseErr;
        }
      }
      throw e;
    }
  },
};

// Workflow API - Simplified and Reliable
export const workflowAPI = {
  start: async (inputs: {
    job_title: string;
    company_name: string;
    country_or_region?: string;
    jd_text: string;
    resume_text: string;
    resume_pdf_upload_id?: string;
    projects_text?: string;
    preferred_lang?: 'en' | 'zh';
  }) => {
    console.log('🚀 Starting workflow...');
    // Backend runs Agent 1 (LLM) synchronously; allow up to 2 minutes
    const response = await api.post(
      '/api/v1/workflow/start',
      {
        job_title: inputs.job_title,
        company_name: inputs.company_name,
        country_or_region: inputs.country_or_region || undefined,
        jd_text: inputs.jd_text,
        resume_text: inputs.resume_text,
        resume_pdf_upload_id: inputs.resume_pdf_upload_id || undefined,
        projects_text: inputs.projects_text || undefined,
        preferred_lang: inputs.preferred_lang || 'en',
      },
      { timeout: 120000 }
    );
    console.log('✅ Workflow started:', response.data.workflow_id);
    return response.data;
  },

  getProgress: async (workflow_id: string) => {
    try {
      const response = await api.get(`/api/v1/workflow/progress/${workflow_id}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        // Return pending state for 404
        return {
          status: 'running',
          current_step: 'agent1',
          progress: 0,
          message: 'Workflow is initializing...',
          results: {},
          error: null,
        };
      }
      throw error;
    }
  },

  // Simple polling-based progress tracking (no SSE complexity)
  trackProgress: (
    workflow_id: string,
    onUpdate: (data: any) => void,
    onError?: (error: Error) => void
  ) => {
    let pollInterval: ReturnType<typeof setInterval> | null = null;
    let isActive = true;
    let lastStatus: string | null = null;

    const poll = async () => {
      if (!isActive) return;

      try {
        const data = await workflowAPI.getProgress(workflow_id);
        
        // Only update if status changed or it's a new update
        if (data.status !== lastStatus || data.progress !== undefined) {
          console.log('📊 Progress update:', {
            status: data.status,
            step: data.current_step,
            progress: data.progress,
          });
          lastStatus = data.status;
          onUpdate(data);

          // Stop polling if workflow is finished
          if (data.status === 'completed' || data.status === 'failed') {
            console.log('✅ Workflow finished, stopping polling');
            stop();
          }
        }
      } catch (error: any) {
        console.error('❌ Polling error:', error);
        if (onError) {
          onError(error as Error);
        }
      }
    };

    const stop = () => {
      isActive = false;
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    };

    // Start polling immediately, then every 2 seconds
    console.log('🔄 Starting progress tracking...');
    poll();
    pollInterval = setInterval(poll, 2000);

    return stop;
  },
};

// Interview API
export const interviewAPI = {
  prepare: async (request: any) => {
    const response = await api.post('/api/v1/interview/prepare', request, { timeout: 120000 });
    return response.data;
  },
  getProgress: async (interview_id: string) => {
    const response = await api.get(`/api/v1/interview/progress/${interview_id}`);
    return response.data;
  },
};

// Resume export API
export const resumeExportAPI = {
  generate: async (request: any) => {
    const response = await api.post('/api/v1/resume/generate', request);
    return response.data;
  },
};
