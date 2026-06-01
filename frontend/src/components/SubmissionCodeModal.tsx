import React, { useEffect, useState } from 'react';
import { getSubmission, type SubmissionDetail } from '../api/submissionsApi';
import { VERDICT_COLORS, VERDICT_LABELS } from './VerdictDisplay';

interface SubmissionCodeModalProps {
  submissionId: number | null;
  onClose: () => void;
}

const highlight = (code: string, language: string) => {
  const escapeHtml = (text: string) =>
    text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  const escaped = escapeHtml(code);
  const lang = language ? language.toLowerCase() : '';

  if (lang === 'python') {
    return escaped
      .replace(/\b(def|class|return|if|else|elif|for|while|import|from|in|is|and|or|not|try|except|with|as|pass|lambda|None|True|False)\b/g, '<span style="color: #2563eb; font-weight: bold;">$1</span>')
      .replace(/("(.*?)"|'(.*?)')/g, '<span style="color: #15803d;">$1</span>')
      .replace(/(#.*)/g, '<span style="color: #9ca3af; font-style: italic;">$1</span>')
      .replace(/\b(\d+)\b/g, '<span style="color: #b45309;">$1</span>');
  } else if (lang === 'cpp' || lang === 'java') {
    return escaped
      .replace(/\b(int|double|float|char|void|class|struct|public|private|protected|static|const|return|if|else|for|while|switch|case|break|continue|new|delete|include|import|package|public|class|interface|extends|implements)\b/g, '<span style="color: #2563eb; font-weight: bold;">$1</span>')
      .replace(/("(.*?)"|'(.*?)')/g, '<span style="color: #15803d;">$1</span>')
      .replace(/(\/\/.*|\/\*[\s\S]*?\*\/)/g, '<span style="color: #9ca3af; font-style: italic;">$1</span>')
      .replace(/\b(\d+)\b/g, '<span style="color: #b45309;">$1</span>');
  }

  return escaped;
};

export default function SubmissionCodeModal({
  submissionId,
  onClose,
}: SubmissionCodeModalProps) {
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (!submissionId) return;

    const fetchDetail = async () => {
      setIsLoading(true);
      try {
        const res = await getSubmission(submissionId);
        setSubmission(res.data);
      } catch (err) {
        console.error('Error fetching submission detail:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetail();
  }, [submissionId]);

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!submissionId) return null;

  return (
    <div
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
    >
      <div className="flex max-h-[85vh] w-full max-w-4xl flex-col rounded-xl border border-gray-100 bg-white shadow-2xl transition-all duration-300">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              Submission #{submissionId}
            </h3>
            {submission && (
              <p className="mt-1 text-xs text-gray-500">
                Submitted by {submission.user}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded bg-gray-50 p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <span className="sr-only">Close</span>
            <span className="text-sm font-bold px-1">✕</span>
          </button>
        </div>

        {/* Modal Content */}
        <div className="overflow-y-auto p-6">
          {isLoading || !submission ? (
            <div className="animate-pulse space-y-4">
              <div className="h-6 w-1/4 rounded bg-gray-200" />
              <div className="h-48 w-full rounded bg-gray-200" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Badges and Metrics */}
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded bg-indigo-50 px-2.5 py-1 text-xs font-semibold uppercase text-indigo-700">
                  {submission.language}
                </span>

                <span
                  className="rounded px-2.5 py-1 text-xs font-semibold text-white"
                  style={{
                    backgroundColor:
                      VERDICT_COLORS[
                        submission.verdict ? submission.verdict.toUpperCase() : ''
                      ] || '#6b7280',
                  }}
                >
                  {VERDICT_LABELS[
                    submission.verdict ? submission.verdict.toUpperCase() : ''
                  ] ||
                    submission.verdict ||
                    submission.status}
                </span>

                {submission.time_ms !== null && (
                  <span className="text-xs text-gray-400">
                    Time: {submission.time_ms}ms
                  </span>
                )}

                {submission.memory_kb !== null && (
                  <span className="text-xs text-gray-400">
                    Memory: {(submission.memory_kb / 1024).toFixed(1)} MB
                  </span>
                )}
              </div>

              {/* Code block */}
              <div className="relative overflow-hidden rounded-lg border border-gray-200 bg-gray-50 font-mono text-xs">
                <div className="bg-gray-100 px-4 py-2 text-[10px] uppercase font-bold text-gray-500 border-b border-gray-200 flex justify-between items-center">
                  <span>Source Code</span>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(submission.code);
                      alert('Code copied to clipboard!');
                    }}
                    className="text-indigo-600 hover:text-indigo-700 bg-white px-2 py-0.5 rounded border border-gray-200 shadow-sm"
                  >
                    Copy
                  </button>
                </div>
                <pre className="overflow-auto p-4 max-h-[50vh] leading-relaxed text-gray-800">
                  <code
                    dangerouslySetInnerHTML={{
                      __html: highlight(submission.code, submission.language),
                    }}
                  />
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
