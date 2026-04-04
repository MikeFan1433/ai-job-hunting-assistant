import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { workflowAPI, healthAPI, resumeAPI } from '../services/api';
import { FileText, Briefcase, ArrowRight, Loader2, AlertCircle, CheckCircle2, Upload } from 'lucide-react';
import { getUiStrings } from '../i18n/uiStrings';
import type { UiLang } from '../i18n/uiStrings';

const PAGE_BG = '#1A1D20';
const CARD_BG = '#2B3037';

export default function InputPage() {
  const navigate = useNavigate();
  const { inputs, setInputs, setWorkflow, resetRetry, workflow } = useAppStore();
  const ui = getUiStrings(inputs.preferred_lang);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [uploadingPDF, setUploadingPDF] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isSubmittingRef = useRef(false);
  const langLocked = loading || workflow.status === 'running';

  useEffect(() => {
    const current = useAppStore.getState().inputs;
    setInputs({
      job_title: '',
      company_name: '',
      country_or_region: '',
      jd_text: '',
      resume_text: '',
      projects_text: '',
      preferred_lang: current.preferred_lang || 'en',
    });

    const checkBackend = async () => {
      if (isSubmittingRef.current) {
        const isOnline = await healthAPI.check();
        if (isOnline) setBackendStatus('online');
        return;
      }
      setBackendStatus('checking');
      const isOnline = await healthAPI.check();
      setBackendStatus(isOnline ? 'online' : 'offline');
    };

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, [setInputs]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputs.job_title.trim() || !inputs.jd_text.trim() || !inputs.resume_text.trim()) {
      setError(ui.input.errRequired);
      return;
    }

    setLoading(true);
    setError(null);
    resetRetry();
    isSubmittingRef.current = true;

    try {
      const response = await workflowAPI.start({
        job_title: inputs.job_title.trim(),
        company_name: (inputs.company_name || '').trim() || inputs.job_title.trim(),
        country_or_region: inputs.country_or_region?.trim() || undefined,
        jd_text: inputs.jd_text,
        resume_text: inputs.resume_text,
        projects_text: inputs.projects_text?.trim() ? inputs.projects_text.trim().slice(0, 1000) : undefined,
        preferred_lang: inputs.preferred_lang,
      });

      if (!response || !response.workflow_id) {
        throw new Error(ui.input.errInvalid);
      }

      setWorkflow({
        workflow_id: response.workflow_id,
        status: 'running',
        current_step: 'agent1',
        progress: 0,
        message: ui.loading.starting,
        results: {},
        error: null,
      });

      navigate('/loading');
    } catch (err: any) {
      isSubmittingRef.current = false;
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 400 && detail && Array.isArray(detail.issues)) {
        setError(detail.issues.join('\n'));
      } else if (status === 400 && detail?.issues) {
        setError(Array.isArray(detail.issues) ? detail.issues.join('\n') : String(detail.issues));
      } else if (status === 0 || err.message?.includes('Network error') || err.code === 'ERR_NETWORK') {
        setError(ui.input.errNetwork);
      } else if (status === 500) {
        setError(ui.input.err500);
      } else if (detail && typeof detail === 'string') {
        setError(detail);
      } else {
        setError(err.message || ui.input.errStart);
      }
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError(ui.input.errTimeout);
      }
      setLoading(false);
    } finally {
      isSubmittingRef.current = false;
    }
  };

  const handlePDFUpload = async (file: File) => {
    if (!file.type.includes('pdf')) {
      setError(ui.input.errPdfType);
      return;
    }
    setUploadingPDF(true);
    setError(null);
    try {
      const result = await resumeAPI.uploadPDF(file);
      if (result.extracted_text) {
        setInputs({ resume_text: result.extracted_text });
      } else {
        setError(ui.input.errPdfExtract);
      }
    } catch (err: any) {
      setError(err.message || ui.input.errUpload);
    } finally {
      setUploadingPDF(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handlePDFUpload(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file?.type.includes('pdf')) handlePDFUpload(file);
    else setError(ui.input.errDropPdf);
  };

  const inputBase =
    'w-full px-4 py-2.5 rounded-lg bg-[#1A1D20] border border-gray-600 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all';
  const textareaBase = inputBase + ' resize-y min-h-[120px]';

  const setLang = (l: UiLang) => {
    if (langLocked) return;
    setInputs({ preferred_lang: l });
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: PAGE_BG }}>
      {/* Progress: 3 steps + language */}
      <div className="flex flex-wrap items-center justify-center gap-4 py-6 px-4">
        <div className="flex items-center justify-center gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-full bg-blue-600 text-white flex items-center justify-center font-medium">1</div>
            <span className="text-white font-medium">{ui.input.stepUpload}</span>
          </div>
          <div className="w-12 border-t border-dashed border-gray-500 hidden sm:block" />
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-full bg-blue-600 text-white flex items-center justify-center font-medium">2</div>
            <span className="text-white font-medium">{ui.input.stepJob}</span>
          </div>
          <div className="w-12 border-t border-dashed border-gray-500 hidden sm:block" />
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-full bg-yellow-500/80 text-gray-900 flex items-center justify-center font-medium">3</div>
            <span className="text-gray-400 font-medium">{ui.input.stepAi}</span>
          </div>
        </div>
        <div
          className="flex items-center gap-2 border border-gray-600 rounded-lg p-0.5 bg-[#1A1D20]"
          title={langLocked ? ui.input.langLockedHint : undefined}
        >
          <span className="text-xs text-gray-500 pl-2 pr-1">{ui.input.langLabel}</span>
          <button
            type="button"
            disabled={langLocked}
            onClick={() => setLang('en')}
            className={`px-3 py-1.5 rounded-md text-sm font-semibold transition-colors ${
              inputs.preferred_lang === 'en'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white'
            } ${langLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {ui.input.langEn}
          </button>
          <button
            type="button"
            disabled={langLocked}
            onClick={() => setLang('zh')}
            className={`px-3 py-1.5 rounded-md text-sm font-semibold transition-colors ${
              inputs.preferred_lang === 'zh'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white'
            } ${langLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {ui.input.langZh}
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 max-w-6xl w-full mx-auto px-4 pb-10 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: 1 简历内容 */}
        <div className="rounded-xl p-6 space-y-4" style={{ backgroundColor: CARD_BG }}>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            {ui.input.resumeSection}
          </h2>
          <div
            className="border-2 border-dashed border-gray-500 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition-colors"
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
          >
            <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileSelect} className="hidden" />
            {uploadingPDF ? (
              <div className="flex items-center justify-center gap-2 text-gray-300">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span>{ui.input.uploadParsing}</span>
              </div>
            ) : (
              <>
                <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-300 mb-1">{ui.input.uploadHint}</p>
                <p className="text-xs text-gray-500">{ui.input.uploadFormats}</p>
              </>
            )}
          </div>
          <textarea
            className={textareaBase}
            placeholder={ui.input.resumePlaceholder}
            value={inputs.resume_text}
            onChange={(e) => setInputs({ resume_text: e.target.value })}
            rows={14}
          />
        </div>

        {/* Right: 2 目标职位 */}
        <div className="rounded-xl p-6 space-y-4" style={{ backgroundColor: CARD_BG }}>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-blue-400" />
            {ui.input.jobSection}
          </h2>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              {ui.input.jobTitle} <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              className={inputBase}
              placeholder={ui.input.jobTitlePh}
              value={inputs.job_title}
              onChange={(e) => setInputs({ job_title: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">{ui.input.company}</label>
            <input
              type="text"
              className={inputBase}
              placeholder={ui.input.companyPh}
              value={inputs.company_name}
              onChange={(e) => setInputs({ company_name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              {ui.input.jd} <span className="text-red-400">*</span>
            </label>
            <textarea
              className={textareaBase}
              placeholder={ui.input.jdPh}
              value={inputs.jd_text}
              onChange={(e) => setInputs({ jd_text: e.target.value })}
              rows={10}
            />
          </div>
        </div>

        {/* Full width: status, error, submit */}
        <div className="lg:col-span-2 flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <div className="flex items-center gap-2 text-sm">
            {backendStatus === 'checking' && (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                <span className="text-gray-400">{ui.input.checkingBackend}</span>
              </>
            )}
            {backendStatus === 'online' && (
              <>
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="text-green-400">{ui.input.backendOnline}</span>
              </>
            )}
            {backendStatus === 'offline' && (
              <>
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-red-400">{ui.input.backendOffline}</span>
              </>
            )}
          </div>
          {error && (
            <div className="flex-1 w-full sm:max-w-xl rounded-lg p-3 bg-red-900/30 border border-red-500/50">
              <p className="text-red-200 text-sm whitespace-pre-wrap">{error}</p>
            </div>
          )}
          <button
            type="submit"
            disabled={
              loading ||
              !inputs.job_title.trim() ||
              !inputs.jd_text.trim() ||
              !inputs.resume_text.trim() ||
              backendStatus === 'offline'
            }
            className="px-6 py-3 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shrink-0"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {ui.input.submitting}
              </>
            ) : (
              <>
                {ui.input.submit}
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
