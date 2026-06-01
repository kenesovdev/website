import { useEffect, useState } from 'react';
import { getSubmissions, type SubmissionListItem } from '../api/submissionsApi';
import { VERDICT_COLORS, VERDICT_LABELS } from './VerdictDisplay';
import SubmissionCodeModal from './SubmissionCodeModal';

interface SubmissionHistoryProps {
  problemId: string;
  refreshTrigger?: number;
}

export default function SubmissionHistory({
  problemId,
  refreshTrigger,
}: SubmissionHistoryProps) {
  const [submissions, setSubmissions] = useState<SubmissionListItem[]>([]);
  const [count, setCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedSubId, setSelectedSubId] = useState<number | null>(null);

  const fetchSubmissions = async () => {
    setIsLoading(true);
    try {
      // Pass problemId and page query parameters matching the backend implementation
      const res = await getSubmissions({
        problem: problemId,
        page,
      } as any);
      setSubmissions(res.data.results);
      setCount(res.data.count);
    } catch (err) {
      console.error('Error fetching submission history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSubmissions();
  }, [problemId, page, refreshTrigger]);

  const totalPages = Math.ceil(count / 20) || 1;

  const handleRowClick = (subId: number) => {
    setSelectedSubId(subId);
  };

  if (isLoading && submissions.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900">Submissions History</h2>
        <div className="animate-pulse space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-12 w-full rounded bg-gray-100" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-8 space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Submissions History</h2>

      {submissions.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-200 py-10 text-center text-gray-500">
          <p className="text-sm font-medium">No submissions yet</p>
          <p className="text-xs text-gray-400 mt-1">Submit your first solution to get started!</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-100 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-sm text-gray-500">
              <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-700">
                <tr>
                  <th scope="col" className="px-6 py-3">#</th>
                  <th scope="col" className="px-6 py-3">Language</th>
                  <th scope="col" className="px-6 py-3">Verdict</th>
                  <th scope="col" className="px-6 py-3">Time</th>
                  <th scope="col" className="px-6 py-3">Memory</th>
                  <th scope="col" className="px-6 py-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {submissions.map((sub) => {
                  const normVerdict = sub.verdict ? sub.verdict.toUpperCase() : '';
                  const verdictColor = VERDICT_COLORS[normVerdict] || '#6b7280';
                  const verdictLabel = VERDICT_LABELS[normVerdict] || normVerdict || sub.status || 'Pending';

                  const formattedMemory =
                    sub.memory_kb !== null
                      ? `${(sub.memory_kb / 1024).toFixed(1)} MB`
                      : '—';

                  const dateStr = new Date(sub.created_at).toLocaleString();

                  return (
                    <tr
                      key={sub.id}
                      onClick={() => handleRowClick(sub.id)}
                      className="cursor-pointer transition-colors duration-150 hover:bg-indigo-50/40 odd:bg-white even:bg-gray-50/30"
                    >
                      <td className="px-6 py-4 font-mono font-medium text-gray-900">
                        {sub.id}
                      </td>
                      <td className="px-6 py-4 capitalize">{sub.language}</td>
                      <td className="px-6 py-4">
                        {sub.status === 'judging' || sub.status === 'pending' ? (
                          <span className="inline-flex items-center gap-1.5 rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                            <span className="h-1.5 w-1.5 animate-ping rounded-full bg-blue-600" />
                            Judging
                          </span>
                        ) : (
                          <span
                            className="inline-block rounded px-2 py-0.5 text-xs font-semibold text-white"
                            style={{ backgroundColor: verdictColor }}
                          >
                            {verdictLabel}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {sub.time_ms !== null ? `${sub.time_ms}ms` : '—'}
                      </td>
                      <td className="px-6 py-4">{formattedMemory}</td>
                      <td className="px-6 py-4 text-xs text-gray-400">{dateStr}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t border-gray-100 px-6 py-4 text-xs text-gray-500">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="rounded border border-gray-200 bg-white px-3 py-1.5 font-medium hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <span className="font-semibold text-gray-700">
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded border border-gray-200 bg-white px-3 py-1.5 font-medium hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {selectedSubId && (
        <SubmissionCodeModal
          submissionId={selectedSubId}
          onClose={() => setSelectedSubId(null)}
        />
      )}
    </div>
  );
}
