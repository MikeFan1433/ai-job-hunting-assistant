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
  
  // 5. Development mode: Use empty string to leverage Vite proxy
  // Check if we're in development mode (Vite dev server)
  // In dev mode, Vite proxy will forward /api requests to http://localhost:8000
  if (import.meta.env.DEV || import.meta.env.MODE === 'development') {
    // Use empty string to use same origin (Vite dev server)
    // Vite proxy will handle /api/* requests
    console.log('🔧 Development mode detected, using Vite proxy (same origin)');
    return ''; // Empty string means same origin, Vite proxy will handle it
  }
  
  // 6. Development: If accessing via IP address, use same IP for backend
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    const devUrl = `http://${hostname}:8000`;
    console.log('🔧 Development IP detected, using:', devUrl);
    return devUrl;
  }
  
  // 7. Default: localhost for development
  const localhostUrl = 'http://localhost:8000';
  console.log('🔧 Localhost development, using:', localhostUrl);
  return localhostUrl;
};

// Get API base URL - call function each time to ensure fresh value
// Note: getCurrentApiBaseUrl is no longer needed, using getApiBaseUrl() directly

// Get initial API base URL
const getInitialApiBaseUrl = () => {
  const url = getApiBaseUrl();
  // If empty (dev mode), use window.location.origin so axios uses same origin
  // Vite proxy will handle /api/* requests
  return url || window.location.origin;
};

const api = axios.create({
  baseURL: getInitialApiBaseUrl(), // Initial value, will be updated in interceptor
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000, // 3 minutes timeout (180 seconds) - workflow start can take time
});

// Request interceptor - dynamically update baseURL for each request
api.interceptors.request.use(
  (config: any) => {
    // Always use fresh API URL for each request
    const currentApiUrl = getApiBaseUrl();
    // If empty (dev mode), use window.location.origin so axios uses same origin
    // Vite proxy will handle /api/* requests
    config.baseURL = currentApiUrl || window.location.origin;
    // Log for debugging (only in development or when needed)
    if (import.meta.env.DEV || window.location.hostname.includes('ai-builders.space')) {
      console.log('API request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        baseURL: currentApiUrl || '(using Vite proxy)',
        fullURL: `${config.baseURL}${config.url}`
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
    // Enhanced error logging
    console.error('❌ API Error:', {
      message: error.message,
      code: error.code,
      config: {
        method: error.config?.method?.toUpperCase(),
        url: error.config?.url,
        baseURL: error.config?.baseURL,
        fullURL: `${error.config?.baseURL || ''}${error.config?.url || ''}`,
        timeout: error.config?.timeout,
      },
      response: error.response ? {
        status: error.response.status,
        data: error.response.data,
      } : null,
      request: error.request ? 'Request made but no response' : null,
    });
    
    if (error.response) {
      // Server responded with error
      return Promise.reject({
        message: error.response.data?.detail || error.response.data?.error || 'An error occurred',
        status: error.response.status,
        data: error.response.data,
      });
    } else if (error.request) {
      // Request made but no response - could be timeout, network issue, or CORS
      let errorMessage = 'Network error. Please check your connection.';
      
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = 'Request timeout. The server is taking too long to respond. Please try again.';
      } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        errorMessage = 'Network error. Please check your internet connection and try again.';
      } else if (error.message?.includes('CORS')) {
        errorMessage = 'CORS error. Please contact the administrator.';
      }
      
      return Promise.reject({
        message: errorMessage,
        status: 0,
        code: error.code,
        originalError: error.message,
      });
    } else {
      // Something else happened
      return Promise.reject({
        message: error.message || 'An unexpected error occurred',
        status: 0,
        code: error.code,
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
      // If apiUrl is empty (dev mode with proxy), use relative path
      const healthPath = apiUrl ? `${apiUrl}/api/v1/health` : '/api/v1/health';
      console.log('🔍 Health check - API URL:', apiUrl || '(using Vite proxy)');
      console.log('🔍 Health check - Full URL:', healthPath);
      
      // Create a fresh axios instance with the current API URL
      const healthCheckClient = axios.create({
        baseURL: apiUrl || window.location.origin, // Use origin if empty (for proxy)
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
    console.log('🚀 Starting workflow with inputs:', {
      jd_length: inputs.jd_text.length,
      resume_length: inputs.resume_text.length,
      projects_length: inputs.projects_text?.length || 0,
    });
    const apiUrl = getApiBaseUrl();
    console.log('🚀 Workflow start API URL:', `${apiUrl}/api/v1/workflow/start`);
    
    try {
      const response = await api.post('/api/v1/workflow/start', inputs);
      console.log('✅ Workflow started successfully:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('❌ Workflow start failed:', error);
      throw error;
    }
  },

  getProgress: async (workflow_id: string) => {
    try {
      const response = await api.get(`/api/v1/workflow/progress/${workflow_id}`);
      return response.data;
    } catch (error: any) {
      // Handle 404 specifically - workflow might not be created yet
      if (error.status === 404) {
        console.warn('Workflow not found, might be initializing:', workflow_id);
        // Return a pending state instead of throwing
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
    let consecutiveErrors = 0;
    const MAX_CONSECUTIVE_ERRORS = 5; // Allow some 404s during initialization

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
          consecutiveErrors = 0; // Reset on success
          onUpdate(data);
          
          if (data.status === 'completed' || data.status === 'failed') {
            close();
          }
        } catch (error: any) {
          consecutiveErrors++;
          console.error('Polling error:', error);
          
          // If workflow not found and we've tried multiple times, show error
          if (error.status === 404 && consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
            console.error('Workflow not found after multiple attempts:', workflow_id);
            if (onError) {
              onError(new Error('Workflow not found. Please start again.'));
            }
            close();
            return;
          }
          
          // For other errors or initial 404s, just log and continue
          if (error.status !== 404 && onError) {
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
        // Check connection state
        const readyState = eventSource?.readyState;
        console.warn('SSE error:', {
          readyState,
          error,
          message: readyState === EventSource.CLOSED ? 'Connection closed' : 'Connection error'
        });
        
        // Only trigger fallback if connection is actually closed
        // EventSource.OPEN = 1, EventSource.CONNECTING = 0, EventSource.CLOSED = 2
        if (readyState === EventSource.CLOSED && !sseFailed && !isClosed) {
          sseFailed = true;
          // Fallback to polling if SSE fails
          console.log('SSE connection closed, falling back to polling (this is normal if proxy doesn\'t support SSE)');
          // Don't show error for SSE fallback - it's expected behavior
          // Polling will handle updates silently
          startPolling();
        } else if (readyState === EventSource.CONNECTING) {
          // Still connecting, don't do anything yet
          console.log('SSE still connecting...');
        }
        
        // Only close if connection is actually closed
        if (readyState === EventSource.CLOSED && eventSource) {
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
