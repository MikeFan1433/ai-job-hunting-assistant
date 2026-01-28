import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { workflowAPI, healthAPI, resumeAPI } from '../services/api';
import { FileText, Briefcase, FolderOpen, ArrowRight, Loader2, AlertCircle, CheckCircle2, Upload } from 'lucide-react';

export default function InputPage() {
  const navigate = useNavigate();
  const { inputs, setInputs, setWorkflow, resetRetry } = useAppStore();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [uploadingPDF, setUploadingPDF] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      setBackendStatus('checking');
      const isOnline = await healthAPI.check();
      setBackendStatus(isOnline ? 'online' : 'offline');
    };
    
    checkBackend();
    // Check every 10 seconds
    const interval = setInterval(checkBackend, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputs.jd_text.trim() || !inputs.resume_text.trim()) {
      setError('Please fill in at least JD and Resume fields');
      return;
    }

    setLoading(true);
    setError(null);
    resetRetry();

    try {
      // Start workflow
      const response = await workflowAPI.start({
        jd_text: inputs.jd_text,
        resume_text: inputs.resume_text,
        projects_text: inputs.projects_text || undefined,
      });

      setWorkflow({
        workflow_id: response.workflow_id,
        status: 'running',
        current_step: 'agent1',
        progress: 0,
        message: 'Starting workflow...',
        results: {},
        error: null,
      });

      // Navigate to loading page
      navigate('/loading');
    } catch (err: any) {
      console.error('Workflow start error:', err);
      let errorMessage = 'Failed to start workflow';
      
      if (err.status === 0 || err.message?.includes('Network error') || err.message?.includes('connection')) {
        errorMessage = '无法连接到后端服务。请确保后端服务正在运行（端口 8000）。\n\nNetwork error: Cannot connect to backend service. Please ensure the backend is running on port 8000.';
      } else if (err.message) {
        errorMessage = err.message;
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handlePDFUpload = async (file: File) => {
    if (!file.type.includes('pdf')) {
      setError('Please upload a PDF file');
      return;
    }

    setUploadingPDF(true);
    setError(null);

    try {
      const result = await resumeAPI.uploadPDF(file);
      if (result.extracted_text) {
        setInputs({ resume_text: result.extracted_text });
        setError(null);
      } else {
        setError('Failed to extract text from PDF');
      }
    } catch (err: any) {
      console.error('PDF upload error:', err);
      setError(err.message || 'Failed to upload PDF. Please try pasting the text instead.');
    } finally {
      setUploadingPDF(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handlePDFUpload(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.includes('pdf')) {
      handlePDFUpload(file);
    } else {
      setError('Please drop a PDF file');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI Job Hunting Assistant
          </h1>
          <p className="text-gray-600 mb-4">
            Get personalized resume optimization and interview preparation
          </p>
          
          {/* Backend Status Indicator */}
          <div className="flex items-center justify-center gap-2 text-sm">
            {backendStatus === 'checking' && (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                <span className="text-gray-500">Checking backend connection...</span>
              </>
            )}
            {backendStatus === 'online' && (
              <>
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span className="text-green-600">Backend connected</span>
              </>
            )}
            {backendStatus === 'offline' && (
              <>
                <AlertCircle className="w-4 h-4 text-red-600" />
                <span className="text-red-600">
                  Backend offline - Please start the backend service (port 8000)
                </span>
              </>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* JD Input */}
          <div className="card">
            <label className="flex items-center gap-2 text-lg font-semibold text-gray-700 mb-3">
              <Briefcase className="w-5 h-5 text-primary-600" />
              Job Description (JD)
              <span className="text-red-500">*</span>
            </label>
            <textarea
              className="textarea"
              placeholder="Paste the job description here..."
              value={inputs.jd_text}
              onChange={(e) => setInputs({ jd_text: e.target.value })}
              rows={8}
              required
            />
            <p className="text-sm text-gray-500 mt-2">
              {inputs.jd_text.length} characters
            </p>
          </div>

          {/* Resume Input */}
          <div className="card">
            <label className="flex items-center gap-2 text-lg font-semibold text-gray-700 mb-3">
              <FileText className="w-5 h-5 text-primary-600" />
              Resume
              <span className="text-red-500">*</span>
            </label>
            
            {/* PDF Upload Section */}
            <div 
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 mb-4 text-center cursor-pointer hover:border-primary-500 transition-colors"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
              />
              {uploadingPDF ? (
                <div className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
                  <span className="text-gray-600">Uploading and parsing PDF...</span>
                </div>
              ) : (
                <div>
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600 mb-1">
                    Click to upload or drag and drop PDF resume
                  </p>
                  <p className="text-xs text-gray-500">or paste text below</p>
                </div>
              )}
            </div>

            <textarea
              className="textarea"
              placeholder="Or paste your resume text here..."
              value={inputs.resume_text}
              onChange={(e) => setInputs({ resume_text: e.target.value })}
              rows={12}
              required
            />
            <p className="text-sm text-gray-500 mt-2">
              {inputs.resume_text.length} characters
            </p>
          </div>

          {/* Projects Input */}
          <div className="card">
            <label className="flex items-center gap-2 text-lg font-semibold text-gray-700 mb-3">
              <FolderOpen className="w-5 h-5 text-primary-600" />
              Project Materials (Optional)
            </label>
            <textarea
              className="textarea"
              placeholder="Paste your project materials here (optional)..."
              value={inputs.projects_text}
              onChange={(e) => setInputs({ projects_text: e.target.value })}
              rows={10}
            />
            <p className="text-sm text-gray-500 mt-2">
              {inputs.projects_text.length} characters
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || !inputs.jd_text.trim() || !inputs.resume_text.trim() || backendStatus === 'offline'}
              className="btn btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  Start Analysis
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
