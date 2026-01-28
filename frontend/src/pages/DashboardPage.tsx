import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { resumeAPI, interviewAPI } from '../services/api';
import { 
  BarChart3, User, Briefcase, FileText, CheckCircle, 
  ArrowRight, Download, Loader2 
} from 'lucide-react';
import MatchAnalysisTab from '../components/dashboard/MatchAnalysisTab';
import CandidateProfileTab from '../components/dashboard/CandidateProfileTab';
import WorkScenarioTab from '../components/dashboard/WorkScenarioTab';
import ProjectsTab from '../components/dashboard/ProjectsTab';
import ResumeOptimizationTab from '../components/dashboard/ResumeOptimizationTab';

type TabType = 'match' | 'profile' | 'scenario' | 'projects' | 'resume';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { workflow, interview, setInterview, setCurrentPage } = useAppStore();
  const [activeTab, setActiveTab] = useState<TabType>('match');
  const [recommendations, setRecommendations] = useState<any>(null);
  const [feedbackStatus, setFeedbackStatus] = useState<any>(null);
  const [generatingResume, setGeneratingResume] = useState(false);
  const [preparingInterview, setPreparingInterview] = useState(false);

  useEffect(() => {
    // Redirect if workflow not completed
    if (workflow.status !== 'completed') {
      navigate('/');
      return;
    }

    // Load recommendations
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

  const handleGenerateResume = async () => {
    setGeneratingResume(true);
    try {
      const result = await resumeAPI.generateFinal();
      useAppStore.getState().setFinalResume(result.final_resume);
      
      // Auto-start Agent 5
      await handleStartInterview();
    } catch (error: any) {
      alert(`Error generating resume: ${error.message}`);
    } finally {
      setGeneratingResume(false);
    }
  };

  const handleStartInterview = async () => {
    if (!workflow.workflow_id) return;

    setPreparingInterview(true);
    try {
      const response = await interviewAPI.prepare(workflow.workflow_id);
      
      setInterview({
        interview_id: response.interview_id,
        status: 'running',
        progress: 0,
        message: 'Preparing interview materials...',
        result: null,
        error: null,
      });

      // Poll for progress
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
          } else if (progress.status === 'failed') {
            clearInterval(pollInterval);
            setPreparingInterview(false);
            alert(`Interview preparation failed: ${progress.error}`);
          }
        } catch (error) {
          clearInterval(pollInterval);
          setPreparingInterview(false);
        }
      }, 2000);

      // Cleanup after 5 minutes
      setTimeout(() => clearInterval(pollInterval), 5 * 60 * 1000);
    } catch (error: any) {
      alert(`Error starting interview preparation: ${error.message}`);
      setPreparingInterview(false);
    }
  };

  const handleExportResume = async (format: 'pdf' | 'docx') => {
    try {
      await resumeAPI.export(format, 'Resume');
      // In a real app, you'd download the file
      alert(`Resume exported successfully! (${format.toUpperCase()})`);
    } catch (error: any) {
      alert(`Error exporting resume: ${error.message}`);
    }
  };

  const tabs = [
    { id: 'match' as TabType, label: 'Match Analysis', icon: BarChart3 },
    { id: 'profile' as TabType, label: 'Candidate Profile', icon: User },
    { id: 'scenario' as TabType, label: 'Work Scenario', icon: Briefcase },
    { id: 'projects' as TabType, label: 'Projects', icon: FileText },
    { id: 'resume' as TabType, label: 'Resume Optimization', icon: CheckCircle },
  ];

  const renderTabContent = () => {
    const agent2Results = workflow.results?.agent2 || {};
    const agent3Results = workflow.results?.agent3 || {};
    const agent4Results = workflow.results?.agent4 || recommendations;

    switch (activeTab) {
      case 'match':
        return <MatchAnalysisTab data={agent2Results} />;
      case 'profile':
        return <CandidateProfileTab data={agent2Results} />;
      case 'scenario':
        return <WorkScenarioTab data={agent2Results} />;
      case 'projects':
        return <ProjectsTab data={agent3Results} />;
      case 'resume':
        return (
          <ResumeOptimizationTab
            data={agent4Results}
            onFeedbackUpdate={loadFeedbackStatus}
            feedbackStatus={feedbackStatus}
          />
        );
      default:
        return null;
    }
  };

  const isInterviewReady = interview.status === 'completed' && interview.result;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <div className="flex items-center gap-4">
              {useAppStore.getState().final_resume && (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExportResume('pdf')}
                    className="btn btn-outline text-sm"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export PDF
                  </button>
                  <button
                    onClick={() => handleExportResume('docx')}
                    className="btn btn-outline text-sm"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export DOCX
                  </button>
                </div>
              )}
              {isInterviewReady && (
                <button
                  onClick={() => {
                    setCurrentPage('interview');
                    navigate('/interview');
                  }}
                  className="btn btn-primary flex items-center gap-2"
                >
                  Interview Prep
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar - Tabs */}
          <div className="col-span-3">
            <div className="card space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary-50 text-primary-700 font-semibold'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Action Panel */}
            {activeTab === 'resume' && (
              <div className="card mt-4">
                <h3 className="font-semibold text-gray-900 mb-4">Actions</h3>
                <div className="space-y-3">
                  <button
                    onClick={handleGenerateResume}
                    disabled={generatingResume || !feedbackStatus || feedbackStatus.pending_feedback > 0}
                    className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {generatingResume ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      'Confirm & Generate Resume'
                    )}
                  </button>
                  
                  {preparingInterview && (
                    <div className="text-sm text-gray-600 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Preparing interview materials...
                    </div>
                  )}

                  {feedbackStatus && (
                    <div className="text-sm text-gray-600">
                      <p>Progress: {feedbackStatus.feedback_received}/{feedbackStatus.total_recommendations}</p>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all"
                          style={{ width: `${feedbackStatus.completion_percentage}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Main Content */}
          <div className="col-span-9">
            <div className="card min-h-[600px]">
              {renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
