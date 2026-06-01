import { useSubmissionStatus, useSubmissionStatusPolling } from '../hooks/useSubmissionStatus';

interface Props {
  submissionId: number | null;
}

const VERDICT_STYLES: Record<string, string> = {
  AC: 'bg-emerald-100 text-emerald-800',
  WA: 'bg-red-100 text-red-800',
  TLE: 'bg-orange-100 text-orange-800',
  MLE: 'bg-orange-100 text-orange-800',
  RE: 'bg-red-100 text-red-800',
  CE: 'bg-yellow-100 text-yellow-800',
};

export default function SubmissionStatus({ submissionId }: Props) {
  const { status: wsStatus, wsFailed } = useSubmissionStatus(submissionId);
  const polledStatus = useSubmissionStatusPolling(submissionId, wsFailed);
  const status = wsStatus ?? polledStatus;

  if (!submissionId) {
    return null;
  }

  if (!status) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
        Connecting…
      </div>
    );
  }

  const isRunning = status.status === 'pending' || status.status === 'judging';

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      {isRunning && (
        <div className="mb-3 flex items-center gap-2 text-sm text-gray-600">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          {status.status === 'pending' ? 'Queued…' : 'Judging…'}
        </div>
      )}

      {status.status === 'error' && (
        <span className="inline-flex rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">
          Judge error
        </span>
      )}

      {status.verdict && (
        <span
          className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
            VERDICT_STYLES[status.verdict] ?? 'bg-gray-100 text-gray-700'
          }`}
        >
          {status.verdict}
        </span>
      )}

      {(status.time_ms != null || status.memory_kb != null) && (
        <div className="mt-2 flex gap-4 text-xs text-gray-500">
          {status.time_ms != null && <span>⏱ {status.time_ms} ms</span>}
          {status.memory_kb != null && <span>💾 {status.memory_kb} KB</span>}
        </div>
      )}

      {wsFailed && isRunning && (
        <p className="mt-2 text-xs text-gray-400">Polling every 2s (WebSocket unavailable)</p>
      )}
    </div>
  );
}
