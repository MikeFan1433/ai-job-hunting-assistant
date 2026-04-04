import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { interviewAPI } from '../services/api';
import { MessageSquare, FolderOpen, Briefcase, ArrowLeft, Loader2, Brain } from 'lucide-react';
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
    if (interview.status === 'completed' && interview.result) {
      setInterviewData(interview.result);
    } else if (interview.status === 'running' && interview.interview_id) {
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
          if (progress.status === 'completed') setInterviewData(progress.result);
          else if (progress.status === 'failed') {
            clearInterval(pollInterval);
            alert(`面试准备失败: ${progress.error}`);
          }
        } catch (error) {
          clearInterval(pollInterval);
        }
      }, 2000);
      return () => clearInterval(pollInterval);
    } else {
      navigate('/dashboard');
    }
  }, [interview, navigate, setInterview]);

  const tabs = [
    { id: 'behavioral' as InterviewTabType, label: '通用问题', icon: MessageSquare },
    { id: 'projects' as InterviewTabType, label: '业务问题', icon: FolderOpen },
    { id: 'business' as InterviewTabType, label: '业务领域', icon: Briefcase },
  ];

  const renderTabContent = () => {
    if (!interviewData) {
      return (
        <div className="text-center py-12">
          <Loader2 className="w-16 h-16 text-purple-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">{interview.message || '正在加载面试材料...'}</p>
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
    <div className="min-h-screen bg-[#1A1D20]">
      <header className="bg-[#252A30] border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => {
                setCurrentPage('dashboard');
                navigate('/dashboard');
              }}
              className="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              返回报告
            </button>
            <h1 className="text-xl font-bold text-white">面试准备</h1>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-7 h-7 text-purple-400" />
            核心问答脚本
          </h2>
        </div>

        <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-700 pb-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white hover:bg-[#2B3037]'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="rounded-xl bg-[#252A30] border border-gray-700 p-6 min-h-[500px]">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}
