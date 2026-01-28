import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { interviewAPI } from '../services/api';
import { MessageSquare, FolderOpen, Briefcase, ArrowLeft, Loader2 } from 'lucide-react';
import BehavioralInterviewTab from '../components/interview/BehavioralInterviewTab';
import ProjectDeepDiveTab from '../components/interview/ProjectDeepDiveTab';
import BusinessDomainTab from '../components/interview/BusinessDomainTab';

type InterviewTabType = 'behavioral' | 'projects' | 'business';

export default function InterviewPage() {
  const navigate = useNavigate();
  const { interview, setInterview, setCurrentPage } = useAppStore();
  const [activeTab, setActiveTab] = useState<InterviewTabType>('behavioral');
  const [interviewData, setInterviewData] = useState<any>(null);

  useEffect(() => {
    // If interview is completed, load result
    if (interview.status === 'completed' && interview.result) {
      setInterviewData(interview.result);
    } else if (interview.status === 'running' && interview.interview_id) {
      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const progress = await interviewAPI.getProgress(interview.interview_id!);
          setInterview({
            status: progress.status,
            progress: progress.progress,
            message: progress.message,
            result: progress.result,
            error: progress.error,
          });

          if (progress.status === 'completed') {
            setInterviewData(progress.result);
            clearInterval(pollInterval);
          } else if (progress.status === 'failed') {
            clearInterval(pollInterval);
            alert(`Interview preparation failed: ${progress.error}`);
          }
        } catch (error) {
          clearInterval(pollInterval);
        }
      }, 2000);

      return () => clearInterval(pollInterval);
    } else {
      // No interview data, redirect to dashboard
      navigate('/dashboard');
    }
  }, [interview, navigate, setInterview]);

  const tabs = [
    { id: 'behavioral' as InterviewTabType, label: 'Behavioral Interview', icon: MessageSquare },
    { id: 'projects' as InterviewTabType, label: 'Project Deep-Dive', icon: FolderOpen },
    { id: 'business' as InterviewTabType, label: 'Business Domain', icon: Briefcase },
  ];

  const renderTabContent = () => {
    if (!interviewData) {
      return (
        <div className="text-center py-12">
          <Loader2 className="w-16 h-16 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">{interview.message || 'Loading interview materials...'}</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'behavioral':
        return <BehavioralInterviewTab data={interviewData.theme_1_behavioral_interview} />;
      case 'projects':
        return <ProjectDeepDiveTab data={interviewData.theme_2_project_deep_dive} />;
      case 'business':
        return <BusinessDomainTab data={interviewData.theme_3_business_domain} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => {
                  setCurrentPage('dashboard');
                  navigate('/dashboard');
                }}
                className="btn btn-outline flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Interview Preparation</h1>
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
          </div>

          {/* Main Content */}
          <div className="col-span-9">
            <div className="card min-h-[600px]">{renderTabContent()}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
