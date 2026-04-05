import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { getUiStrings } from '../i18n/uiStrings';
import { resumeAPI, interviewAPI } from '../services/api';
import { 
  BarChart3, User, Briefcase, CheckCircle, 
  TrendingUp, MessageSquare
} from 'lucide-react';
import MatchAnalysisTab from '../components/dashboard/MatchAnalysisTab';
import CandidateProfileTab from '../components/dashboard/CandidateProfileTab';
import WorkScenarioTab from '../components/dashboard/WorkScenarioTab';
import ResumeOptimizationTab from '../components/dashboard/ResumeOptimizationTab';
import InterviewPrepTab from '../components/dashboard/InterviewPrepTab';

type TabType = 'scenario' | 'profile' | 'match' | 'resume' | 'interview';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { workflow, setInterview, inputs, setInputs, final_resume: finalResumeFromStore } = useAppStore();
  const ui = useMemo(() => getUiStrings(inputs.preferred_lang), [inputs.preferred_lang]);
  const langLocked = Boolean(workflow.workflow_id);
  const [activeTab, setActiveTab] = useState<TabType>('scenario');
  const [recommendations, setRecommendations] = useState<any>(null);
  const [feedbackStatus, setFeedbackStatus] = useState<any>(null);
  const [generatingResume, setGeneratingResume] = useState(false);
  const [preparingInterview, setPreparingInterview] = useState(false);
  const [generatedResume, setGeneratedResume] = useState<string | null>(null);
  const [interviewData, setInterviewData] = useState<any>(null);

  // Lifted state: survives tab switches (persisted in parent)
  const [userFeedback, setUserFeedback] = useState<Record<string, string>>({});
  const [editedTexts, setEditedTexts] = useState<Record<string, string>>({});
  const [confirmedModifications, setConfirmedModifications] = useState(false);
  const [exportingResumeFormat, setExportingResumeFormat] = useState<'pdf' | 'docx' | null>(null);

  useEffect(() => {
    if (workflow.status !== 'completed') {
      navigate('/');
      return;
    }
    loadRecommendations();
    loadFeedbackStatus();
  }, [workflow.status, navigate]);

  const loadRecommendations = async () => {
    try {
      const data = await resumeAPI.getRecommendations();
      setRecommendations(data.recommendations);
    } catch (error: any) {
      console.error('Error loading recommendations:', error);
    }
  };

  const loadFeedbackStatus = async () => {
    try {
      const data = await resumeAPI.getFeedbackStatus();
      setFeedbackStatus(data.feedback_status);
    } catch (error: any) {
      console.error('Error loading feedback status:', error);
    }
  };

  const handleConfirmModifications = async (feedbackMap: Record<string, { action: string; text?: string }>) => {
    setGeneratingResume(true);
    try {
      const batchPayload = Object.entries(feedbackMap).map(([itemId, fb]) => ({
        feedback_type: 'bullet_suggestion',
        item_id: itemId,
        feedback: fb.action === 'accept' ? 'accept' : fb.action === 'edited' ? 'further_modify' : 'reject',
        modified_text: fb.text,
      }));

      try {
        await resumeAPI.submitBatchFeedback(batchPayload);
      } catch {
        // Backend batch endpoint may not be available yet; continue with generation
      }

      const result = await resumeAPI.generateFinal();
      const finalResume = result.final_resume;
      useAppStore.getState().setFinalResume(finalResume);
      setGeneratedResume(finalResume);
      setGeneratingResume(false);
      setConfirmedModifications(true);

      await handleStartInterview();
    } catch (error: any) {
      alert(`${ui.dashboard.genResumeFail} ${error.message}`);
      setGeneratingResume(false);
    }
  };

  const handleStartInterview = async () => {
    if (!workflow.workflow_id) return;

    setPreparingInterview(true);
    try {
      const response = await interviewAPI.prepare({ workflow_id: workflow.workflow_id! });

      setInterview({
        interview_id: response.interview_id,
        status: 'running',
        progress: 0,
        message: ui.dashboard.interviewStarting,
        result: null,
        error: null,
      });

      const pollInterval = setInterval(async () => {
        try {
          const progress = await interviewAPI.getProgress(response.interview_id);
          setInterview({
            status: progress.status,
            progress: progress.progress,
            message: progress.message,
            result: progress.result,
            error: progress.error,
          });

          if (progress.status === 'completed') {
            clearInterval(pollInterval);
            setPreparingInterview(false);
            if (progress.result) {
              setInterviewData(progress.result);
            }
          } else if (progress.status === 'failed') {
            clearInterval(pollInterval);
            setPreparingInterview(false);
          }
        } catch {
          clearInterval(pollInterval);
          setPreparingInterview(false);
        }
      }, 2000);

      setTimeout(() => clearInterval(pollInterval), 5 * 60 * 1000);
    } catch (error: any) {
      alert(`面试准备启动失败: ${error.message}`);
      setPreparingInterview(false);
    }
  };

  const handleExportResume = async (format: 'pdf' | 'docx') => {
    setExportingResumeFormat(format);
    try {
      await resumeAPI.export(format, 'Resume');
    } catch (error: any) {
      alert(`${ui.dashboard.exportErr} ${error.message}`);
    } finally {
      setExportingResumeFormat(null);
    }
  };

  const agent5FromWorkflow = workflow.results?.agent5;
  const agent5Results = interviewData || agent5FromWorkflow;

  const tabs = [
    { id: 'scenario' as TabType, label: ui.dashboard.tabScenario, icon: Briefcase, color: 'green' },
    { id: 'profile' as TabType, label: ui.dashboard.tabProfile, icon: User, color: 'purple' },
    { id: 'match' as TabType, label: ui.dashboard.tabMatch, icon: BarChart3, color: 'blue' },
    { id: 'resume' as TabType, label: ui.dashboard.tabResume, icon: CheckCircle, color: 'indigo' },
    { id: 'interview' as TabType, label: ui.dashboard.tabInterview, icon: MessageSquare, color: 'purple' },
  ];

  const renderTabContent = () => {
    const agent2Results = workflow.results?.agent2 || {};
    const agent4Results = workflow.results?.agent4 || recommendations;

    switch (activeTab) {
      case 'match':
        return <MatchAnalysisTab data={agent2Results} />;
      case 'profile':
        return <CandidateProfileTab data={agent2Results} />;
      case 'scenario':
        return <WorkScenarioTab data={agent2Results} />;
      case 'resume':
        return (
          <ResumeOptimizationTab
            workflowId={workflow.workflow_id}
            data={agent4Results}
            onFeedbackUpdate={loadFeedbackStatus}
            feedbackStatus={feedbackStatus}
            onExportResume={handleExportResume}
            exportingResumeFormat={exportingResumeFormat}
            hasFinalResume={Boolean(generatedResume || finalResumeFromStore)}
            onConfirmModifications={handleConfirmModifications}
            generatingResume={generatingResume}
            preparingInterview={preparingInterview}
            generatedResume={generatedResume}
            confirmedModifications={confirmedModifications}
            userFeedback={userFeedback}
            setUserFeedback={setUserFeedback}
            editedTexts={editedTexts}
            setEditedTexts={setEditedTexts}
          />
        );
      case 'interview':
        return (
          <InterviewPrepTab
            data={agent5Results}
            preparingInterview={preparingInterview}
            confirmedModifications={confirmedModifications}
          />
        );
      default:
        return null;
    }
  };

  const stats = [
    {
      label: ui.dashboard.statLabel,
      value: workflow.status === 'completed' ? ui.dashboard.statDone : ui.dashboard.statRunning,
      icon: TrendingUp,
      color: 'green',
      bgGradient: 'from-green-500 to-teal-600'
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30">
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                {ui.dashboard.title}
              </h1>
              <p className="text-sm text-gray-400 mt-1">{ui.dashboard.subtitle}</p>
            </div>
            <div
              className="flex items-center gap-2 border border-gray-200 rounded-lg p-0.5 bg-gray-50/80"
              title={langLocked ? ui.input.langLockedHint : undefined}
            >
              <span className="text-xs text-gray-500 pl-2 pr-1">{ui.input.langLabel}</span>
              <button
                type="button"
                disabled={langLocked}
                onClick={() => setInputs({ preferred_lang: 'en' })}
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                  inputs.preferred_lang === 'en'
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {ui.input.langEn}
              </button>
              <button
                type="button"
                disabled={langLocked}
                onClick={() => setInputs({ preferred_lang: 'zh' })}
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                  inputs.preferred_lang === 'zh'
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {ui.input.langZh}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div
                key={index}
                className="group relative overflow-hidden bg-white rounded-xl shadow-sm border border-gray-200/50 p-6 hover:shadow-lg transition-all duration-300"
              >
                <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${stat.bgGradient} opacity-5 group-hover:opacity-10 transition-opacity`}
                />
                <div className="relative">
                  <div className="flex items-center justify-between mb-3">
                    <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${stat.bgGradient} flex items-center justify-center shadow-md`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <p className="text-sm font-medium text-gray-600 mb-1">{stat.label}</p>
                  <p className={`text-2xl font-bold ${
                    stat.color === 'green' ? 'text-green-600' :
                    stat.color === 'yellow' ? 'text-yellow-600' :
                    stat.color === 'red' ? 'text-red-600' :
                    stat.color === 'blue' ? 'text-blue-600' :
                    'text-purple-600'
                  }`}>
                    {stat.value}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Modern Sidebar - Tabs */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 p-4 space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-r from-primary-50 to-blue-50 text-primary-700 font-semibold shadow-sm border border-primary-200/50'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      isActive 
                        ? `bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-md` 
                        : 'bg-gray-100 text-gray-600'
                    } transition-all`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-sm">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-9">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 p-8 min-h-[600px]">
              <div className="animate-in fade-in duration-300">
                {renderTabContent()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
