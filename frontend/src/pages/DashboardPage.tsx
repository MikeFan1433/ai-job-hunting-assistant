import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { resumeAPI, interviewAPI } from '../services/api';
import { 
  BarChart3, User, Briefcase, FileText, CheckCircle, 
  ArrowRight, Download, Loader2, Sparkles, TrendingUp, Award, Target
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
    { id: 'match' as TabType, label: 'Match Analysis', icon: BarChart3, color: 'blue' },
    { id: 'profile' as TabType, label: 'Candidate Profile', icon: User, color: 'purple' },
    { id: 'scenario' as TabType, label: 'Work Scenario', icon: Briefcase, color: 'green' },
    { id: 'projects' as TabType, label: 'Projects', icon: FileText, color: 'orange' },
    { id: 'resume' as TabType, label: 'Resume Optimization', icon: CheckCircle, color: 'indigo' },
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
  const matchScore = parseFloat(workflow.results?.agent2?.match_assessment?.overall_match_score || '0');
  const hasRecommendations = recommendations && recommendations.length > 0;
  const hasProjects = workflow.results?.agent3 && Object.keys(workflow.results.agent3).length > 0;

  // Get stats for overview cards
  const stats = [
    {
      label: 'Match Score',
      value: matchScore > 0 ? `${matchScore.toFixed(1)}/5.0` : 'N/A',
      icon: Target,
      color: matchScore >= 4 ? 'green' : matchScore >= 3 ? 'yellow' : 'red',
      bgGradient: matchScore >= 4 
        ? 'from-green-500 to-emerald-600' 
        : matchScore >= 3 
        ? 'from-yellow-500 to-orange-500' 
        : 'from-red-500 to-pink-600'
    },
    {
      label: 'Recommendations',
      value: hasRecommendations ? `${recommendations.length}` : '0',
      icon: Sparkles,
      color: 'blue',
      bgGradient: 'from-blue-500 to-cyan-600'
    },
    {
      label: 'Projects',
      value: hasProjects ? 'Ready' : 'Pending',
      icon: Award,
      color: 'purple',
      bgGradient: 'from-purple-500 to-indigo-600'
    },
    {
      label: 'Status',
      value: workflow.status === 'completed' ? 'Complete' : 'Processing',
      icon: TrendingUp,
      color: 'green',
      bgGradient: 'from-green-500 to-teal-600'
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30">
      {/* Modern Header with Gradient */}
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Dashboard
                </h1>
                <p className="text-sm text-gray-500 mt-0.5">Your personalized job hunting insights</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {useAppStore.getState().final_resume && (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExportResume('pdf')}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    PDF
                  </button>
                  <button
                    onClick={() => handleExportResume('docx')}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    DOCX
                  </button>
                </div>
              )}
              {isInterviewReady && (
                <button
                  onClick={() => {
                    setCurrentPage('interview');
                    navigate('/interview');
                  }}
                  className="px-5 py-2.5 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg font-medium hover:from-primary-700 hover:to-primary-800 transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
                >
                  Interview Prep
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
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

            {/* Action Panel */}
            {activeTab === 'resume' && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 p-6 mt-4">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-primary-600" />
                  Actions
                </h3>
                <div className="space-y-3">
                  <button
                    onClick={handleGenerateResume}
                    disabled={generatingResume || !feedbackStatus || feedbackStatus.pending_feedback > 0}
                    className="w-full px-4 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg font-medium hover:from-primary-700 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
                  >
                    {generatingResume ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        Confirm & Generate Resume
                      </>
                    )}
                  </button>
                  
                  {preparingInterview && (
                    <div className="text-sm text-gray-600 flex items-center gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                      Preparing interview materials...
                    </div>
                  )}

                  {feedbackStatus && (
                    <div className="text-sm text-gray-600 space-y-2 p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Progress</span>
                        <span className="text-primary-600 font-semibold">
                          {feedbackStatus.feedback_received}/{feedbackStatus.total_recommendations}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-primary-500 to-primary-600 h-2.5 rounded-full transition-all duration-500 shadow-sm"
                          style={{ width: `${feedbackStatus.completion_percentage}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {feedbackStatus.completion_percentage}% complete
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
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
