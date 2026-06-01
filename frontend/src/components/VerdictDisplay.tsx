
interface VerdictDisplayProps {
  status: string;
  verdict: string;
  timeMs?: number | null;
  memoryKb?: number | null;
}

export const VERDICT_COLORS: Record<string, string> = {
  ACCEPTED: '#16a34a',
  AC: '#16a34a',
  WRONG_ANSWER: '#dc2626',
  WA: '#dc2626',
  TIME_LIMIT: '#ca8a04',
  TLE: '#ca8a04',
  MEMORY_LIMIT: '#ea580c',
  MLE: '#ea580c',
  RUNTIME_ERROR: '#9333ea',
  RE: '#9333ea',
  COMPILE_ERROR: '#6b7280',
  CE: '#6b7280',
};

export const VERDICT_LABELS: Record<string, string> = {
  ACCEPTED: 'Accepted',
  AC: 'Accepted',
  WRONG_ANSWER: 'Wrong Answer',
  WA: 'Wrong Answer',
  TIME_LIMIT: 'Time Limit Exceeded',
  TLE: 'Time Limit Exceeded',
  MEMORY_LIMIT: 'Memory Limit Exceeded',
  MLE: 'Memory Limit Exceeded',
  RUNTIME_ERROR: 'Runtime Error',
  RE: 'Runtime Error',
  COMPILE_ERROR: 'Compilation Error',
  CE: 'Compilation Error',
};

export default function VerdictDisplay({
  status,
  verdict,
  timeMs,
  memoryKb,
}: VerdictDisplayProps) {
  const normStatus = status ? status.toUpperCase() : '';
  const normVerdict = verdict ? verdict.toUpperCase() : '';

  const isPending = normStatus === 'PENDING' || normStatus === 'JUDGING';

  if (isPending) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-blue-700">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        <span className="animate-pulse font-semibold">Judging...</span>
      </div>
    );
  }

  // Find colored background style or default to gray
  const color = VERDICT_COLORS[normVerdict] || VERDICT_COLORS[normStatus] || '#6b7280';
  const label = VERDICT_LABELS[normVerdict] || VERDICT_LABELS[normStatus] || normVerdict || normStatus || 'Unknown';

  const formattedMemory =
    memoryKb !== undefined && memoryKb !== null
      ? `${(memoryKb / 1024).toFixed(1)} MB`
      : null;

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-gray-100 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-500">Verdict:</span>
        <span
          className="inline-block rounded px-2.5 py-1 text-xs font-semibold text-white transition-colors duration-150"
          style={{ backgroundColor: color }}
        >
          {label}
        </span>
      </div>
      {(timeMs !== undefined && timeMs !== null) || formattedMemory ? (
        <div className="flex gap-4 text-xs text-gray-400">
          {timeMs !== undefined && timeMs !== null && (
            <span>Time: {timeMs}ms</span>
          )}
          {formattedMemory && (
            <span>Memory: {formattedMemory}</span>
          )}
        </div>
      ) : null}
    </div>
  );
}
