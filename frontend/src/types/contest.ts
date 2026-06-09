export type ContestParticipationType = 'OPEN' | 'INVITE_ONLY';
export type ContestStatus = 'UPCOMING' | 'ONGOING' | 'FINISHED';

export interface Contest {
  id: number;
  title: string;
  slug: string;
  type: ContestParticipationType;
  participation_type: ContestParticipationType;
  start_time: string;
  end_time: string;
  status: ContestStatus;
  participant_count: number;
  problem_count: number;
  is_registered: boolean;
}

export interface ContestProblemItem {
  order_label: string;
  order: number;
  points: number;
  xp_reward: number;
  problem: {
    id: string;
    title: string;
    slug: string;
    difficulty: string;
    time_limit: number;
    memory_limit: number;
  };
  user_result: {
    status: string;
    attempts: number;
    ac_time_minutes: number | null;
  } | null;
}

export interface ContestDetail extends Contest {
  description: string;
  created_by: { id: string; handle: string };
  problems: ContestProblemItem[];
}

export interface ContestStandingRow {
  rank: number;
  user_id: string;
  handle: string;
  total_xp: number;
  last_solve_at: string | null;
  joined_at: string;
}

export interface ContestStandings {
  contest_id: number;
  title: string;
  rows: ContestStandingRow[];
}

export interface CreateContestPayload {
  title: string;
  description: string;
  participation_type: ContestParticipationType;
  start_time: string;
  end_time: string;
  is_public: boolean;
  problems: { problem_id: string; order: number; order_label?: string }[];
}

export interface PaginatedContests {
  count: number;
  next: string | null;
  previous: string | null;
  results: Contest[];
}
