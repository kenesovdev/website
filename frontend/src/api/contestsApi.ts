import type {
  ContestDetail,
  ContestStandings,
  CreateContestPayload,
  PaginatedContests,
} from '../types/contest';
import api from './axios';

export const getContests = (params?: { page?: number; status?: string }) =>
  api.get<PaginatedContests>('/contests/', { params });

export const getContest = (id: number) =>
  api.get<ContestDetail>(`/contests/${id}/`);

export const createContest = (payload: CreateContestPayload) =>
  api.post<ContestDetail>('/contests/', payload);

export const joinContest = (id: number) =>
  api.post(`/contests/${id}/join/`);

export const inviteToContest = (id: number, handle: string) =>
  api.post(`/contests/${id}/invite/`, { handle });

export const getContestStandings = (id: number) =>
  api.get<ContestStandings>(`/contests/${id}/standings/`);
