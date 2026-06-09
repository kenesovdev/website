import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { format, formatDistanceStrict } from 'date-fns';
import { ru } from 'date-fns/locale';
import toast from 'react-hot-toast';

import { getContest, getContestStandings, joinContest } from '../api/contestsApi';
import DifficultyBadge from '../components/DifficultyBadge';
import FullPageSpinner from '../components/FullPageSpinner';
import { useAuthStore } from '../store/authStore';

type Tab = 'problems' | 'standings';

function Countdown({ target, label }: { target: Date; label: string }) {
  const [remaining, setRemaining] = useState('');

  useEffect(() => {
    const tick = () => {
      const now = Date.now();
      const diff = target.getTime() - now;
      if (diff <= 0) {
        setRemaining('00:00:00');
        return;
      }
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setRemaining(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [target]);

  return (
    <div className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-indigo-600">{label}</p>
      <p className="mt-1 font-mono text-2xl font-bold text-indigo-900">{remaining}</p>
    </div>
  );
}

export default function ContestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const contestId = Number(id);
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>('problems');

  const { data: contest, isLoading } = useQuery({
    queryKey: ['contest', contestId],
    queryFn: () => getContest(contestId).then((res) => res.data),
    enabled: Number.isFinite(contestId),
  });

  const { data: standings } = useQuery({
    queryKey: ['contest-standings', contestId],
    queryFn: () => getContestStandings(contestId).then((res) => res.data),
    enabled: Number.isFinite(contestId) && tab === 'standings' && contest?.status !== 'UPCOMING',
    refetchInterval: tab === 'standings' && contest?.status === 'ONGOING' ? 30000 : false,
  });

  const joinMutation = useMutation({
    mutationFn: () => joinContest(contestId),
    onSuccess: () => {
      toast.success('Вы присоединились к соревнованию');
      queryClient.invalidateQueries({ queryKey: ['contest', contestId] });
    },
    onError: () => toast.error('Не удалось присоединиться'),
  });

  if (isLoading || !contest) {
    return <FullPageSpinner />;
  }

  const start = new Date(contest.start_time);
  const end = new Date(contest.end_time);
  const countdownTarget = contest.status === 'UPCOMING' ? start : contest.status === 'ONGOING' ? end : null;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <Link to="/contests" className="text-sm text-indigo-600 hover:text-indigo-800">
          ← Все соревнования
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">{contest.title}</h1>
        <p className="mt-1 text-sm text-gray-500">
          {format(start, 'dd MMM yyyy, HH:mm', { locale: ru })}
          {' — '}
          {format(end, 'dd MMM yyyy, HH:mm', { locale: ru })}
          {' · '}
          {formatDistanceStrict(start, end, { locale: ru })}
        </p>
      </div>

      <div className="mb-6 flex flex-wrap items-start gap-4">
        {countdownTarget && (
          <Countdown
            target={countdownTarget}
            label={contest.status === 'UPCOMING' ? 'До начала' : 'До конца'}
          />
        )}
        {!contest.is_registered && contest.status !== 'FINISHED' && (
          <button
            type="button"
            onClick={() => joinMutation.mutate()}
            disabled={joinMutation.isPending}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {joinMutation.isPending ? 'Присоединение…' : 'Присоединиться'}
          </button>
        )}
        {contest.is_registered && (
          <span className="rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm font-medium text-green-700">
            Вы участвуете
          </span>
        )}
        {user?.role === 'admin' && contest.participation_type === 'INVITE_ONLY' && (
          <Link
            to={`/contests/${contest.id}/invite`}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Пригласить
          </Link>
        )}
      </div>

      {contest.description && (
        <div className="prose prose-sm mb-6 max-w-none rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <p className="whitespace-pre-wrap text-gray-700">{contest.description}</p>
        </div>
      )}

      <div className="mb-4 flex gap-2 border-b border-gray-200">
        <button
          type="button"
          onClick={() => setTab('problems')}
          className={`px-4 py-2 text-sm font-medium ${
            tab === 'problems'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Задачи ({contest.problems.length})
        </button>
        <button
          type="button"
          onClick={() => setTab('standings')}
          className={`px-4 py-2 text-sm font-medium ${
            tab === 'standings'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Таблица лидеров
        </button>
      </div>

      {tab === 'problems' && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">Название</th>
                <th className="px-4 py-3">Сложность</th>
                <th className="px-4 py-3">XP</th>
                <th className="px-4 py-3">Статус</th>
              </tr>
            </thead>
            <tbody>
              {contest.problems.map((cp) => (
                <tr key={cp.order_label} className="border-b border-gray-100 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-gray-500">{cp.order_label}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    <Link
                      to={`/problems/${cp.problem.slug}?contest_id=${contest.id}`}
                      className="hover:text-indigo-600"
                    >
                      {cp.problem.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <DifficultyBadge difficulty={cp.problem.difficulty as 'easy' | 'medium' | 'hard' | 'expert'} />
                  </td>
                  <td className="px-4 py-3 text-gray-600">{cp.xp_reward}</td>
                  <td className="px-4 py-3">
                    {cp.user_result?.status === 'AC' ? (
                      <span className="text-green-600 font-medium">✓ Решено</span>
                    ) : cp.user_result ? (
                      <span className="text-gray-500">{cp.user_result.attempts} попыток</span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'standings' && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          {contest.status === 'UPCOMING' ? (
            <p className="px-4 py-8 text-center text-gray-500">Таблица появится после начала</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="px-4 py-3">Место</th>
                  <th className="px-4 py-3">Участник</th>
                  <th className="px-4 py-3">XP</th>
                  <th className="px-4 py-3">Последнее решение</th>
                </tr>
              </thead>
              <tbody>
                {standings?.rows.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                      Пока нет результатов
                    </td>
                  </tr>
                ) : (
                  standings?.rows.map((row) => (
                    <tr key={row.user_id} className="border-b border-gray-100">
                      <td className="px-4 py-3 font-medium text-gray-500">{row.rank}</td>
                      <td className="px-4 py-3">
                        <Link to={`/profile/${row.handle}`} className="font-medium text-indigo-600 hover:text-indigo-800">
                          {row.handle}
                        </Link>
                      </td>
                      <td className="px-4 py-3 font-semibold text-gray-900">{row.total_xp}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {row.last_solve_at
                          ? format(new Date(row.last_solve_at), 'dd MMM HH:mm:ss', { locale: ru })
                          : '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
