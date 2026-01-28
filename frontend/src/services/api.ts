/** API service for backend communication */
import axios from 'axios';

// Auto-detect API base URL based on current hostname
// Priority: VITE_API_BASE_URL env var > same origin > localhost
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  const origin = window.location.origin;
  
  // 1. Check environment variable (for production deployment)
  if (import.meta.env.VITE_API_BASE_URL) {
    console.log('Using VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // 2. CRITICAL: If hostname contains 'ai-builders.space', ALWAYS use same origin
  if (hostname.includes('ai-builders.space')) {
    console.log('✅ ai-builders.space detected, using same origin:', origin);
    return origin;
  }
  
  // 3. Check if we're on a production domain (contains dots and not localhost/IP)
  // Check if it's a domain name (not localhost or IP address)
  const isDomainName = hostname.includes('.') && 
                       hostname !== 'localhost' && 
                       hostname !== '127.0.0.1' &&
                       !hostname.match(/^\d+\.\d+\.\d+\.\d+$/) &&
                       !hostname.startsWith('192.168.') &&
                       !hostname.startsWith('10.') &&
                       !hostname.startsWith('172.');
  
  // If it's a domain name, always use same origin
  if (isDomainName) {
    console.log('✅ Domain detected, using same origin:', origin);
    return origin;
  }
  
  // 4. Check Vite production mode
  if (import.meta.env.PROD || import.meta.env.MODE === 'production') {
    console.log('✅ Production mode detected, using same origin:', origin);
    return origin;
  }
  
  // 5. Development: If accessing via IP address, use same IP for backend
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    const devUrl = `http://${hostname}:8000`;
    console.log('🔧 Development IP detected, using:', devUrl);
    return devUrl;
  }
  
  // 6. Default: localhost for development
  const localhostUrl = 'http://localhost:8000';
  console.log('🔧 Localhost development, using:', localhostUrl);
  return localhostUrl;
};

// Get API base URL - call function each time to ensure fresh value
const getCurrentApiBaseUrl = () => getApiBaseUrl();

const api = axios.create({
  baseURL: getCurrentApiBaseUrl(), // Initial value, will be updated in interceptor
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor - dynamically update baseURL for each request
api.interceptors.request.use(
  (config: any) => {
    // Always use fresh API URL for each request
    const currentApiUrl = getApiBaseUrl();
    config.baseURL = currentApiUrl;
    // Log for debugging (only in development or when needed)
    if (import.meta.env.DEV || window.location.hostname.includes('ai-builders.space')) {
      console.log('API request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        baseURL: currentApiUrl,
        fullURL: `${currentApiUrl}${config.url}`
      });
    }
    return config;
  },
  (error: any) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response: any) => response,
  (error: any) => {
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
      const healthUrl = `${apiUrl}/api/v1/health`;
      console.log('🔍 Health check - API URL:', apiUrl);
      console.log('🔍 Health check - Full URL:', healthUrl);
      
      // Create a fresh axios instance with the current API URL
      const healthCheckClient = axios.create({
        baseURL: apiUrl,
        timeout: 15000, // 15 second timeout (increased)
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const response = await healthCheckClient.get('/api/v1/health');
      const isHealthy = response.status === 200 && response.data?.status === 'healthy';
      console.log('✅ Health check result:', isHealthy ? 'HEALTHY' : 'UNHEALTHY', response.data);
      return isHealthy;
    } catch (error: any) {
      console.error('❌ Health check failed:', error);
      if (error.config) {
        console.error('❌ Health check attempted URL:', error.config.baseURL || error.config.url);
        console.error('❌ Full attempted URL:', `${error.config.baseURL || ''}${error.config.url || ''}`);
      }
      if (error.response) {
        console.error('❌ Health check response status:', error.response.status);
        console.error('❌ Health check response data:', error.response.data);
      }
      if (error.request) {
        console.error('❌ Health check - No response received. Request details:', error.request);
      }
      if (error.message) {
        console.error('❌ Health check error message:', error.message);
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

    // Try SSE first - use fresh API URL
    try {
      const apiUrl = getApiBaseUrl();
      console.log('SSE connection using URL:', apiUrl);
      eventSource = new EventSource(`${apiUrl}/api/v1/workflow/progress/${workflow_id}/stream`);
      
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
      // Immediately start polling as fallback
      console.log('SSE creation failed, starting polling immediately');
      startPolling();
    }
    
    // Also start polling as backup after a short delay
    // This ensures we get updates even if SSE silently fails
    setTimeout(() => {
      if (!sseFailed && !isClosed && !pollInterval) {
        console.log('Starting polling as backup to SSE');
        startPolling();
      }
    }, 3000);

    return close;
  },
};

// Resume API
export const resumeAPI = {
  uploadPDF: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const apiUrl = getApiBaseUrl();
    const response = await axios.post(`${apiUrl}/api/v1/upload/resume-pdf`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 30000,
    });
    return response.data;
  },

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
