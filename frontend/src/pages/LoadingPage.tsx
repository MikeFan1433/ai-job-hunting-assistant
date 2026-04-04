import { useEffect, useState, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { workflowAPI } from '../services/api';
import { Loader2, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { getUiStrings } from '../i18n/uiStrings';

const STEP_ORDER = ['agent1', 'agent2', 'agent3', 'agent4', 'agent5'] as const;

/** Backend still runs agent3; UI hides that row and keeps “step 2” active until agent4. */
function stepIdForProgressDisplay(current: string): (typeof STEP_ORDER)[number] {
  if (current === 'agent3') return 'agent2';
  if (STEP_ORDER.includes(current as (typeof STEP_ORDER)[number])) {
    return current as (typeof STEP_ORDER)[number];
  }
  return 'agent1';
}

export default function LoadingPage() {
  const navigate = useNavigate();
  const { workflow, setWorkflow, incrementRetry, retry_count, inputs } = useAppStore();
  const ui = useMemo(() => getUiStrings(inputs.preferred_lang), [inputs.preferred_lang]);
  const STEPS = useMemo(
    () => [
      { id: 'agent1', label: ui.loading.stepAgent1 },
      { id: 'agent2', label: ui.loading.stepAgent2 },
      { id: 'agent3', label: ui.loading.stepAgent3 },
      { id: 'agent4', label: ui.loading.stepAgent4 },
      { id: 'agent5', label: ui.loading.stepAgent5 },
    ],
    [ui]
  );
  const lastProgressAtRef = useRef<number>(Date.now());
  const [stuckWarning, setStuckWarning] = useState(false);
  const [backendNotActivated, setBackendNotActivated] = useState(false);
  const [displayProgress, setDisplayProgress] = useState(0);
  const targetProgressRef = useRef(0);
  const animFrameRef = useRef<number>();

  // Smooth progress animation: interpolate toward target
  useEffect(() => {
    const animate = () => {
      setDisplayProgress((prev) => {
        const target = targetProgressRef.current;
        if (Math.abs(prev - target) < 0.5) return target;
        return prev + (target - prev) * 0.08;
      });
      animFrameRef.current = requestAnimationFrame(animate);
    };
    animFrameRef.current = requestAnimationFrame(animate);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

  // Sync target progress from workflow state
  useEffect(() => {
    targetProgressRef.current = workflow.progress ?? 0;
  }, [workflow.progress]);

  useEffect(() => {
    if (!workflow.workflow_id) {
      console.warn('No workflow_id, redirecting to home');
      navigate('/');
      return;
    }

    const checkState = async () => {
      try {
        const currentState = await workflowAPI.getProgress(workflow.workflow_id!);
        if ((currentState as any).workflow_found === false) {
          setBackendNotActivated(true);
        } else {
          setBackendNotActivated(false);
        }
        const u2 = getUiStrings(useAppStore.getState().inputs.preferred_lang);
        lastProgressAtRef.current = Date.now();
        setWorkflow({
          status: currentState.status,
          current_step: currentState.current_step || 'agent1',
          progress: currentState.progress ?? 0,
          message: currentState.message || u2.loading.processing,
          results: currentState.results || {},
          error: currentState.error || null,
        });
        if (currentState.status === 'completed') {
          navigate('/dashboard');
          return;
        }
      } catch (error) {
        console.warn('Error checking initial state:', error);
      }
    };
    checkState();

    const stopTracking = workflowAPI.trackProgress(
      workflow.workflow_id!,
      (data) => {
        if ((data as any).workflow_found === false) {
          setBackendNotActivated(true);
        } else {
          setBackendNotActivated(false);
        }
        lastProgressAtRef.current = Date.now();
        setStuckWarning(false);
        const u3 = getUiStrings(useAppStore.getState().inputs.preferred_lang);
        setWorkflow({
          status: data.status,
          current_step: data.current_step || 'agent1',
          progress: data.progress ?? 0,
          message: data.message || u3.loading.processing,
          results: data.results || {},
          error: data.error || null,
        });
        if (data.status === 'completed') {
          navigate('/dashboard');
        }
      },
      (error) => {
        console.error('Tracking error:', error);
      }
    );

    const stuckCheckInterval = setInterval(() => {
      const { workflow: w } = useAppStore.getState();
      const timeSinceLastUpdate = Date.now() - lastProgressAtRef.current;
      if (timeSinceLastUpdate > 120000 && w.status === 'running') {
        setStuckWarning(true);
      }
    }, 10000);

    return () => {
      stopTracking();
      clearInterval(stuckCheckInterval);
    };
  }, [workflow.workflow_id, navigate, setWorkflow, inputs.preferred_lang]);

  const handleRetry = async () => {
    const ru = getUiStrings(useAppStore.getState().inputs.preferred_lang);
    if (retry_count >= 3) {
      alert(ru.loading.retryMax);
      navigate('/');
      return;
    }
    incrementRetry();
    setWorkflow({ status: 'running', progress: 0, message: ru.loading.retrying });
    try {
      const { inputs } = useAppStore.getState();
      const ru2 = getUiStrings(inputs.preferred_lang);
      const response = await workflowAPI.start({
        job_title: inputs.job_title,
        company_name: inputs.company_name,
        country_or_region: inputs.country_or_region || undefined,
        jd_text: inputs.jd_text,
        resume_text: inputs.resume_text,
        projects_text: inputs.projects_text || undefined,
        preferred_lang: inputs.preferred_lang,
      });
      setWorkflow({
        workflow_id: response.workflow_id,
        status: 'running',
        current_step: 'agent1',
        progress: 0,
        message: ru2.loading.starting,
        results: {},
        error: null,
      });
    } catch (error: any) {
      const ruE = getUiStrings(useAppStore.getState().inputs.preferred_lang);
      setWorkflow({
        status: 'failed',
        error: error.message || ruE.loading.retryFailed,
      });
    }
  };

  const visibleSteps = STEPS.filter((s) => s.id !== 'agent3');
  const progressStepId = stepIdForProgressDisplay(workflow.current_step || 'agent1');
  const progressOrderIndex = STEP_ORDER.indexOf(progressStepId);

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
            {workflow.status === 'running' && ui.loading.running}
            {workflow.status === 'completed' && ui.loading.completed}
            {workflow.status === 'failed' && ui.loading.failed}
          </h1>

          {/* Progress Bar */}
          {workflow.status === 'running' && (
            <div className="mb-6 mt-4">
              <div className="w-full bg-gray-200 rounded-full h-3 mb-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-primary-500 to-primary-600 h-3 rounded-full transition-none"
                  style={{ width: `${Math.min(displayProgress, 100)}%` }}
                />
              </div>
              <p className="text-sm text-gray-500">{Math.round(displayProgress)}%</p>
            </div>
          )}

          {/* Message */}
          <p className="text-gray-700 mb-6">{workflow.message || ui.loading.processing}</p>

          {/* Backend not activated */}
          {backendNotActivated && workflow.status === 'running' && (
            <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 mb-6 text-left">
              <p className="text-amber-900 font-semibold mb-2">⚠️ {ui.loading.backendWarnTitle}</p>
              <p className="text-amber-800 text-sm mb-3">{ui.loading.backendWarnBody}</p>
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm hover:bg-amber-700"
              >
                {ui.loading.backendWarnBtn}
              </button>
            </div>
          )}

          {/* Stuck Warning */}
          {stuckWarning && workflow.status === 'running' && !backendNotActivated && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6 text-left">
              <p className="text-orange-800 font-semibold mb-2">⚠️ {ui.loading.stuckTitle}</p>
              <p className="text-orange-700 text-sm mb-3">{ui.loading.stuckBody}</p>
              <div className="flex gap-2">
                <button onClick={() => window.location.reload()} className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700">
                  {ui.loading.refresh}
                </button>
                <button onClick={() => navigate('/')} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg text-sm hover:bg-gray-300">
                  {ui.loading.restart}
                </button>
              </div>
            </div>
          )}

          {/* Error Display */}
          {workflow.status === 'failed' && workflow.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
              <p className="text-red-800 font-semibold mb-2">{ui.loading.errorLabel}</p>
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
                {ui.loading.retryBtn(retry_count, 3)}
              </button>
            </div>
          )}

          {/* Steps Progress */}
          {workflow.status === 'running' && (
            <div className="mt-8 space-y-3">
              {visibleSteps.map((step, visibleIndex) => {
                const orderIdx = STEP_ORDER.indexOf(step.id as (typeof STEP_ORDER)[number]);
                const isActive =
                  workflow.current_step === step.id ||
                  (workflow.current_step === 'agent3' && step.id === 'agent2');
                const isCompleted =
                  workflow.current_step === 'completed' ||
                  (progressOrderIndex >= 0 && orderIdx >= 0 && progressOrderIndex > orderIdx);

                return (
                  <div key={step.id} className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors duration-300 ${
                        isCompleted
                          ? 'bg-green-600 text-white'
                          : isActive
                          ? 'bg-primary-600 text-white animate-pulse'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      {isCompleted ? '✓' : visibleIndex + 1}
                    </div>
                    <span
                      className={`text-sm ${
                        isActive
                          ? 'text-primary-700 font-semibold'
                          : isCompleted
                          ? 'text-green-700'
                          : 'text-gray-400'
                      }`}
                    >
                      {step.label}
                    </span>
                    {isActive && <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />}
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
