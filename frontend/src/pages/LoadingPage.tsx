import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { workflowAPI } from '../services/api';
import { Loader2, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

export default function LoadingPage() {
  const navigate = useNavigate();
  const { workflow, setWorkflow, incrementRetry, retry_count } = useAppStore();
  const [, setPolling] = useState(true); // Used in useEffect and handleRetry
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastUpdateTime, setLastUpdateTime] = useState<number>(Date.now());
  const [stuckWarning, setStuckWarning] = useState(false);

  useEffect(() => {
    if (!workflow.workflow_id) {
      console.warn('No workflow_id, redirecting to home');
      navigate('/');
      return;
    }

    console.log('LoadingPage: Starting progress tracking for workflow:', workflow.workflow_id);

    // Start SSE stream for real-time updates with error handling
    const cleanup = workflowAPI.streamProgress(
      workflow.workflow_id!,
      (data) => {
        console.log('LoadingPage: Progress update received:', data);
        setLastUpdateTime(Date.now());
        setConnectionError(null); // Clear error on successful update
        setStuckWarning(false);
        
        setWorkflow({
          status: data.status,
          current_step: data.current_step,
          progress: data.progress,
          message: data.message,
          results: data.results || {},
          error: data.error,
        });

        // Navigate to dashboard when completed
        if (data.status === 'completed') {
          console.log('LoadingPage: Workflow completed, navigating to dashboard');
          setPolling(false);
          setTimeout(() => {
            navigate('/dashboard');
          }, 1000);
        }

        // Handle failure
        if (data.status === 'failed') {
          console.error('LoadingPage: Workflow failed:', data.error);
          setPolling(false);
        }
      },
      (error) => {
        // Handle connection errors
        console.error('LoadingPage: Connection error:', error);
        setConnectionError(error.message);
        // Don't set status to failed, just show warning
        // The polling fallback will continue trying
      }
    );

    // Check for stuck workflow (no updates for 2 minutes)
    const stuckCheckInterval = setInterval(() => {
      const timeSinceLastUpdate = Date.now() - lastUpdateTime;
      if (timeSinceLastUpdate > 120000 && workflow.status === 'running') {
        console.warn('LoadingPage: Workflow appears stuck, no updates for', Math.floor(timeSinceLastUpdate / 1000), 'seconds');
        setStuckWarning(true);
      }
    }, 10000); // Check every 10 seconds

    return () => {
      console.log('LoadingPage: Cleaning up progress tracking');
      cleanup();
      clearInterval(stuckCheckInterval);
    };
  }, [workflow.workflow_id, navigate, setWorkflow, lastUpdateTime, workflow.status]);

  const handleRetry = async () => {
    if (retry_count >= 3) {
      alert('Maximum retry attempts reached. Please start over.');
      navigate('/');
      return;
    }

    incrementRetry();
    setPolling(true);
    setWorkflow({ status: 'running', progress: 0, message: 'Retrying...' });

    try {
      const { inputs } = useAppStore.getState();
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
    } catch (error: any) {
      setWorkflow({
        status: 'failed',
        error: error.message || 'Failed to retry workflow',
      });
      setPolling(false);
    }
  };

  const getStepName = (step: string) => {
    const steps: Record<string, string> = {
      agent1: 'Input Validation',
      agent2: 'JD Analysis',
      agent3: 'Project Packaging',
      agent4: 'Resume Optimization',
      completed: 'Completed',
    };
    return steps[step] || step;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="card text-center">
          {/* Status Icon */}
          <div className="mb-6">
            {workflow.status === 'running' && (
              <Loader2 className="w-16 h-16 text-primary-600 animate-spin mx-auto" />
            )}
            {workflow.status === 'completed' && (
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto" />
            )}
            {workflow.status === 'failed' && (
              <XCircle className="w-16 h-16 text-red-600 mx-auto" />
            )}
          </div>

          {/* Title */}
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {workflow.status === 'running' && 'Processing Your Request...'}
            {workflow.status === 'completed' && 'Analysis Complete!'}
            {workflow.status === 'failed' && 'Processing Failed'}
          </h1>

          {/* Current Step */}
          {workflow.status === 'running' && (
            <p className="text-lg text-gray-600 mb-6">
              {getStepName(workflow.current_step)}
            </p>
          )}

          {/* Progress Bar */}
          {workflow.status === 'running' && (
            <div className="mb-6">
              <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                <div
                  className="bg-primary-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${workflow.progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">{workflow.progress}%</p>
            </div>
          )}

          {/* Message */}
          <p className="text-gray-700 mb-6">{workflow.message || 'Processing...'}</p>

          {/* Stuck Warning */}
          {stuckWarning && workflow.status === 'running' && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6 text-left">
              <p className="text-orange-800 font-semibold mb-2">⚠️ 工作流可能卡住了</p>
              <p className="text-orange-700 text-sm mb-3">
                工作流似乎没有更新。这可能是正常的（处理需要时间），但如果等待时间过长，请尝试刷新页面或重新开始。
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700"
                >
                  刷新页面
                </button>
                <button
                  onClick={() => navigate('/')}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg text-sm hover:bg-gray-300"
                >
                  重新开始
                </button>
              </div>
            </div>
          )}

          {/* Connection Warning - Only show if it's a real error, not SSE fallback */}
          {connectionError && 
           workflow.status === 'running' && 
           !connectionError.includes('SSE') && 
           !connectionError.includes('polling') && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 text-left">
              <p className="text-yellow-800 font-semibold mb-2">⚠️ Connection Warning:</p>
              <p className="text-yellow-700 text-sm">{connectionError}</p>
              <p className="text-yellow-600 text-xs mt-2">Using fallback connection method...</p>
            </div>
          )}

          {/* Debug Info (only in development) */}
          {import.meta.env.DEV && workflow.workflow_id && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-6 text-left text-xs">
              <p className="font-semibold mb-1">Debug Info:</p>
              <p>Workflow ID: {workflow.workflow_id}</p>
              <p>Status: {workflow.status}</p>
              <p>Step: {workflow.current_step}</p>
              <p>Progress: {workflow.progress}%</p>
              <p className="mt-2">
                <a 
                  href={`http://localhost:8000/api/v1/workflow/progress/${workflow.workflow_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  查看 API 响应 →
                </a>
              </p>
            </div>
          )}

          {/* Error Display */}
          {workflow.status === 'failed' && workflow.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
              <p className="text-red-800 font-semibold mb-2">Error:</p>
              <p className="text-red-700">{workflow.error}</p>
            </div>
          )}

          {/* Retry Button */}
          {workflow.status === 'failed' && (
            <div className="space-y-4">
              <button
                onClick={handleRetry}
                disabled={retry_count >= 3}
                className="btn btn-primary flex items-center gap-2 mx-auto disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className="w-5 h-5" />
                {retry_count >= 3 ? 'Max Retries Reached' : `Retry (${retry_count}/3)`}
              </button>
              {retry_count >= 3 && (
                <p className="text-sm text-gray-600">
                  Maximum retry attempts reached. Please start over.
                </p>
              )}
            </div>
          )}

          {/* Steps Progress */}
          {workflow.status === 'running' && (
            <div className="mt-8 space-y-3">
              {['agent1', 'agent2', 'agent3', 'agent4'].map((step, index) => {
                const isActive = workflow.current_step === step;
                const isCompleted = ['agent2', 'agent3', 'agent4'].indexOf(workflow.current_step) > index;
                
                return (
                  <div key={step} className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        isCompleted
                          ? 'bg-green-600 text-white'
                          : isActive
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {isCompleted ? '✓' : index + 1}
                    </div>
                    <span
                      className={`${
                        isActive ? 'text-primary-600 font-semibold' : 'text-gray-600'
                      }`}
                    >
                      {getStepName(step)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
