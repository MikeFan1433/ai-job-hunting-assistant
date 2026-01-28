/** API service for backend communication */
import axios from 'axios';

// Auto-detect API base URL based on current hostname
// Priority: VITE_API_BASE_URL env var > same origin > localhost
const getApiBaseUrl = () => {
  // 1. Check environment variable (for production deployment)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // 2. In production or when not on localhost, use same origin (backend serves frontend)
  // Check if we're in production build or on a remote server
  const hostname = window.location.hostname;
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') || hostname.startsWith('10.') || hostname.startsWith('172.');
  const isProduction = import.meta.env.PROD || 
                       import.meta.env.MODE === 'production' ||
                       (!isLocalhost && hostname.includes('.'));
  
  if (isProduction) {
    // In production, backend serves the frontend, so use same origin
    return window.location.origin;
  }
  
  // 3. Development: If accessing via IP address, use same IP for backend
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `http://${hostname}:8000`;
  }
  
  // 4. Default: localhost for development
  return 'http://localhost:8000';
};

// Get API base URL - call function each time to ensure fresh value
const getCurrentApiBaseUrl = () => getApiBaseUrl();

const api = axios.create({
  baseURL: getCurrentApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      return Promise.reject({
        message: error.response.data?.detail || error.response.data?.error || 'An error occurred',
        status: error.response.status,
        data: error.response.data,
      });
    } else if (error.request) {
      // Request made but no response
      return Promise.reject({
        message: 'Network error. Please check your connection.',
        status: 0,
      });
    } else {
      // Something else happened
      return Promise.reject({
        message: error.message || 'An unexpected error occurred',
        status: 0,
      });
    }
  }
);

// Health check API
export const healthAPI = {
  check: async (): Promise<boolean> => {
    try {
      // Get fresh API URL each time
      const apiUrl = getApiBaseUrl();
      console.log('Health check using URL:', apiUrl);
      
      // Create a fresh axios instance with the current API URL
      const healthCheckClient = axios.create({
        baseURL: apiUrl,
        timeout: 10000, // 10 second timeout
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const response = await healthCheckClient.get('/api/v1/health');
      const isHealthy = response.status === 200 && response.data?.status === 'healthy';
      console.log('Health check result:', isHealthy, response.data);
      return isHealthy;
    } catch (error: any) {
      console.error('Health check failed:', error);
      if (error.config) {
        console.error('Health check attempted URL:', error.config.baseURL || error.config.url);
      }
      if (error.response) {
        console.error('Health check response status:', error.response.status);
      }
      return false;
    }
  },
};

// Workflow API
export const workflowAPI = {
  start: async (inputs: { jd_text: string; resume_text: string; projects_text?: string }) => {
    const response = await api.post('/api/v1/workflow/start', inputs);
    return response.data;
  },

  getProgress: async (workflow_id: string) => {
    const response = await api.get(`/api/v1/workflow/progress/${workflow_id}`);
    return response.data;
  },

  getResult: async (workflow_id: string) => {
    const response = await api.get(`/api/v1/workflow/result/${workflow_id}`);
    return response.data;
  },

  // SSE stream for real-time progress with fallback to polling
  streamProgress: (workflow_id: string, onUpdate: (data: any) => void, onError?: (error: Error) => void) => {
    let eventSource: EventSource | null = null;
    let pollInterval: ReturnType<typeof setInterval> | null = null;
    let sseFailed = false;
    let isClosed = false;

    const close = () => {
      isClosed = true;
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    };

    // Fallback polling function
    const startPolling = () => {
      if (pollInterval) return; // Already polling
      
      const poll = async () => {
        if (isClosed) return;
        
        try {
          const data = await workflowAPI.getProgress(workflow_id);
          onUpdate(data);
          
          if (data.status === 'completed' || data.status === 'failed') {
            close();
          }
        } catch (error) {
          console.error('Polling error:', error);
          if (onError) {
            onError(error as Error);
          }
        }
      };
      
      // Poll immediately, then every 2 seconds
      poll();
      pollInterval = setInterval(poll, 2000);
    };

    // Try SSE first
    try {
      eventSource = new EventSource(`${API_BASE_URL}/api/v1/workflow/progress/${workflow_id}/stream`);
      
      eventSource.onopen = () => {
        console.log('SSE connection opened');
        sseFailed = false;
      };
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onUpdate(data);
          
          // Close if completed or failed
          if (data.status === 'completed' || data.status === 'failed') {
            close();
          }
        } catch (error) {
          console.error('Error parsing SSE data:', error);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        if (!sseFailed && !isClosed) {
          sseFailed = true;
          // Fallback to polling if SSE fails
          console.log('SSE failed, falling back to polling');
          if (onError) {
            onError(new Error('SSE connection failed, using polling instead'));
          }
          startPolling();
        }
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
      };
    } catch (error) {
      console.error('Failed to create SSE connection:', error);
      sseFailed = true;
      if (onError) {
        onError(new Error('Failed to create SSE connection'));
      }
      startPolling();
    }

    // If SSE fails immediately, start polling
    setTimeout(() => {
      if (sseFailed && !pollInterval && !isClosed) {
        startPolling();
      }
    }, 3000);

    return close;
  },
};

// Resume API
export const resumeAPI = {
  getRecommendations: async () => {
    const response = await api.get('/api/v1/resume/recommendations');
    return response.data;
  },

  submitFeedback: async (feedback: {
    feedback_type: string;
    item_id: string;
    feedback: string;
    additional_notes?: string;
    modified_text?: string;
  }) => {
    const response = await api.post('/api/v1/resume/feedback', feedback);
    return response.data;
  },

  submitBatchFeedback: async (feedbacks: any[]) => {
    const response = await api.post('/api/v1/resume/feedback/batch', feedbacks);
    return response.data;
  },

  getFeedbackStatus: async () => {
    const response = await api.get('/api/v1/resume/feedback/status');
    return response.data;
  },

  generateFinal: async () => {
    const response = await api.post('/api/v1/resume/generate');
    return response.data;
  },

  export: async (format: 'pdf' | 'docx', title: string = 'Resume') => {
    const response = await api.post('/api/v1/resume/export', { format, title });
    return response.data;
  },
};

// Interview API
export const interviewAPI = {
  prepare: async (workflow_id: string) => {
    const response = await api.post('/api/v1/interview/prepare', { workflow_id });
    return response.data;
  },

  getProgress: async (interview_id: string) => {
    const response = await api.get(`/api/v1/interview/progress/${interview_id}`);
    return response.data;
  },

  getResult: async (interview_id: string) => {
    const response = await api.get(`/api/v1/interview/result/${interview_id}`);
    return response.data;
  },
};

// Projects API
export const projectsAPI = {
  getClassified: async () => {
    const response = await api.get('/api/v1/projects/classified');
    return response.data;
  },
};

export default api;
