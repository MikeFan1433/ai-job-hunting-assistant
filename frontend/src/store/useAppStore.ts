/** Zustand store for global state management */
import { create } from 'zustand';
import type { AppState, UserInputs, WorkflowState, InterviewState } from '../types';

// Simple localStorage persistence (without zustand/middleware for simplicity)
const STORAGE_KEY = 'ai-job-hunting-storage';

interface AppStore extends AppState {
  // Actions
  setInputs: (inputs: Partial<UserInputs>) => void;
  setWorkflow: (workflow: Partial<WorkflowState>) => void;
  setInterview: (interview: Partial<InterviewState>) => void;
  setFinalResume: (resume: string | null) => void;
  setCurrentPage: (page: 'input' | 'dashboard' | 'interview') => void;
  incrementRetry: () => void;
  resetRetry: () => void;
  reset: () => void;
}

const initialState: AppState = {
  inputs: {
    jd_text: '',
    resume_text: '',
    projects_text: '',
  },
  workflow: {
    workflow_id: null,
    status: 'idle',
    current_step: '',
    progress: 0,
    message: '',
    results: {},
    error: null,
  },
  interview: {
    interview_id: null,
    status: 'idle',
    progress: 0,
    message: '',
    result: null,
    error: null,
  },
  final_resume: null,
  current_page: 'input',
  retry_count: 0,
};

// Load from localStorage
const loadFromStorage = (): Partial<AppState> => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Error loading from storage:', error);
  }
  return {};
};

// Save to localStorage
const saveToStorage = (state: AppStore) => {
  try {
    const toSave = {
      inputs: state.inputs,
      workflow: state.workflow,
      interview: state.interview,
      final_resume: state.final_resume,
      current_page: state.current_page,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch (error) {
    console.error('Error saving to storage:', error);
  }
};

const savedState = loadFromStorage();

export const useAppStore = create<AppStore>((set) => ({
  ...initialState,
  ...savedState,

  setInputs: (inputs) => {
    set((state) => {
      const newState = { inputs: { ...state.inputs, ...inputs } };
      saveToStorage({ ...state, ...newState } as AppStore);
      return newState;
    });
  },

  setWorkflow: (workflow) => {
    set((state) => {
      const newState = { workflow: { ...state.workflow, ...workflow } };
      saveToStorage({ ...state, ...newState } as AppStore);
      return newState;
    });
  },

  setInterview: (interview) => {
    set((state) => {
      const newState = { interview: { ...state.interview, ...interview } };
      saveToStorage({ ...state, ...newState } as AppStore);
      return newState;
    });
  },

  setFinalResume: (resume) => {
    set((state) => {
      const newState = { final_resume: resume };
      saveToStorage({ ...state, ...newState } as AppStore);
      return newState;
    });
  },

  setCurrentPage: (page) => {
    set((state) => {
      const newState = { current_page: page };
      saveToStorage({ ...state, ...newState } as AppStore);
      return newState;
    });
  },

  incrementRetry: () =>
    set((state) => ({ retry_count: state.retry_count + 1 })),

  resetRetry: () =>
    set({ retry_count: 0 }),

  reset: () => {
    localStorage.removeItem(STORAGE_KEY);
    set(initialState);
  },
}));
