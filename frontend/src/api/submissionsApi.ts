import api from './axios';

export interface SubmissionListItem {
  id: number;
  problem: string;
  problem_title: string;
  problem_slug: string;
  language: string;
  status: 'pending' | 'judging' | 'done' | 'error';
  verdict: string | null;
  time_ms: number | null;
  memory_kb: number | null;
  created_at: string;
}

export interface SubmissionDetail extends SubmissionListItem {
  user: string;
  code: string;
}

export interface PaginatedSubmissions {
  count: number;
  next: string | null;
  previous: string | null;
  results: SubmissionListItem[];
}

export interface SubmissionFiltersParams {
  problem_id?: string;
  language?: string;
  page?: number;
}

export const getSubmissions = (params?: SubmissionFiltersParams) =>
  api.get<PaginatedSubmissions>('/submissions/', { params });

export const getSubmission = (id: number) =>
  api.get<SubmissionDetail>(`/submissions/${id}/`);

export const createSubmission = (data: {
  problem: string;
  code: string;
  language: string;
}) => api.post<SubmissionDetail>('/submissions/', data);
