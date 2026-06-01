import toast from 'react-hot-toast';
import { VERDICT_COLORS, VERDICT_LABELS } from './VerdictDisplay';

export const showVerdictToast = (verdict: string, timeMs?: number | null) => {
  const normVerdict = verdict ? verdict.toUpperCase() : '';
  const color = VERDICT_COLORS[normVerdict] || '#6b7280';
  const label = VERDICT_LABELS[normVerdict] || normVerdict || 'Verdict Updated';

  const isSuccess = normVerdict === 'AC' || normVerdict === 'ACCEPTED';
  const icon = isSuccess ? '✓' : '✗';

  toast.custom(
    (t) => (
      <div
        className={`${
          t.visible ? 'animate-enter' : 'animate-leave'
        } max-w-sm w-full bg-white shadow-xl rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5 transition-all duration-300`}
        style={{
          borderLeft: `5px solid ${color}`,
          zIndex: 9999,
        }}
      >
        <div className="flex-1 w-0 p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0 pt-0.5">
              <span
                className="inline-flex h-6 w-6 items-center justify-center rounded-full text-sm font-bold text-white"
                style={{ backgroundColor: color }}
              >
                {icon}
              </span>
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-bold text-gray-900">
                {isSuccess ? 'Accepted' : label}
              </p>
              {timeMs !== undefined && timeMs !== null && (
                <p className="mt-1 text-xs text-gray-500">
                  Execution completed in {timeMs}ms
                </p>
              )}
            </div>
            <div className="ml-4 flex flex-shrink-0">
              <button
                type="button"
                onClick={() => toast.dismiss(t.id)}
                className="inline-flex rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                <span className="sr-only">Close</span>
                <span className="text-xs px-1">✕</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    ),
    { duration: 4000, position: 'bottom-right' }
  );
};

export default showVerdictToast;
