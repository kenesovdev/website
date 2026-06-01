import { useEffect, useRef, useState } from 'react';

import { getSubmission } from '../api/submissionsApi';
import { useAuthStore } from '../store/authStore';
import { getWsBaseUrl } from '../utils/apiUrl';

export interface SubmissionStatus {
  submission_id?: number;
  status: 'pending' | 'judging' | 'done' | 'error';
  verdict: string | null;
  time_ms: number | null;
  memory_kb: number | null;
}

function buildWsUrl(submissionId: number, token: string): string {
  const params = new URLSearchParams({ token });
  return `${getWsBaseUrl()}/ws/submissions/${submissionId}/?${params}`;
}

function mapPayload(data: Record<string, unknown>): SubmissionStatus {
  return {
    submission_id: data.submission_id as number | undefined,
    status: data.status as SubmissionStatus['status'],
    verdict: (data.verdict as string | null) ?? null,
    time_ms: (data.time_ms as number | null) ?? null,
    memory_kb: (data.memory_kb as number | null) ?? null,
  };
}

export function useSubmissionStatus(submissionId: number | null) {
  const [status, setStatus] = useState<SubmissionStatus | null>(null);
  const [wsFailed, setWsFailed] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!submissionId) {
      return undefined;
    }

    const token = useAuthStore.getState().accessToken;
    if (!token) {
      return undefined;
    }

    setWsFailed(false);
    const ws = new WebSocket(buildWsUrl(submissionId, token));
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as Record<string, unknown>;
      const next = mapPayload(data);
      setStatus(next);
      if (next.status === 'done' || next.status === 'error') {
        ws.close();
      }
    };

    ws.onerror = () => {
      console.error('WebSocket error for submission', submissionId);
      setWsFailed(true);
    };

    return () => {
      ws.close();
    };
  }, [submissionId]);

  return { status, wsFailed };
}

export function useSubmissionStatusPolling(
  submissionId: number | null,
  enabled: boolean,
) {
  const [status, setStatus] = useState<SubmissionStatus | null>(null);

  useEffect(() => {
    if (!submissionId || !enabled) {
      return undefined;
    }

    let active = true;

    const poll = async () => {
      try {
        const { data } = await getSubmission(submissionId);
        if (!active) {
          return;
        }
        setStatus({
          submission_id: data.id,
          status: data.status,
          verdict: data.verdict,
          time_ms: data.time_ms,
          memory_kb: data.memory_kb,
        });
        if (data.status === 'done' || data.status === 'error') {
          active = false;
        }
      } catch {
        // ignore polling errors
      }
    };

    poll();
    const interval = setInterval(poll, 2000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [submissionId, enabled]);

  return status;
}
