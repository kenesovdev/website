import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

import { getContests } from '../api/contestsApi';
import { useAuthStore } from '../store/authStore';
import type { ContestParticipationType, ContestStatus } from '../types/contest';

const PAGE_SIZE = 20;

function StatusBadge({ status }: { status: ContestStatus }) {
  const styles: Record<ContestStatus, string> = {
    UPCOMING: 'bg-blue-100 text-blue-700',
    ONGOING: 'bg-green-100 text-green-700',
    FINISHED: 'bg-gray-100 text-gray-600',
  };
  const labels: Record<ContestStatus, string> = {
    UPCOMING: 'Предстоящее',
    ONGOING: 'Идёт',
    FINISHED: 'Завершено',
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

function TypeBadge({ type }: { type: ContestParticipationType }) {
  const isOpen = type === 'OPEN';
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
        isOpen ? 'bg-indigo-100 text-indigo-700' : 'bg-amber-100 text-amber-700'
      }`}
    >
      {isOpen ? 'Открытое' : 'По приглашению'}
    </span>
  );
}

function TableSkeleton() {
  return (
    <>
      {Array.from({ length: 6 }).map((_, i) => (
        <tr key={i} className="animate-pulse border-b border-gray-100">
          <td className="px-4 py-4"><div className="h-4 w-6 rounded bg-gray-200" /></td>
          <td className="px-4 py-4"><div className="h-4 w-48 rounded bg-gray-200" /></td>
          <td className="px-4 py-4"><div className="h-5 w-20 rounded-full bg-gray-200" /></td>
          <td className="px-4 py-4"><div className="h-5 w-24 rounded-full bg-gray-200" /></td>
          <td className="px-4 py-4"><div className="h-4 w-28 rounded bg-gray-200" /></td>
          <td className="px-4 py-4"><div className="h-4 w-28 rounded bg-gray-200" /></td>
          <td className="px-4 py-4"><div className="h-4 w-12 rounded bg-gray-200" /></td>
        </tr>
      ))}
    </>
  );
}

export default function ContestsPage() {
  const { user } = useAuthStore();
  const [page, setPage] = useState(1);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['contests', page],
    queryFn: () => getContests({ page }).then((res) => res.data),
    placeholderData: keepPreviousData,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Соревнования</h1>
          {data && (
            <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-sm font-medium text-indigo-700">
              {data.count}
            </span>
          )}
        </div>
        {user?.role === 'admin' && (
          <Link
            to="/contests/create"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Создать
          </Link>
        )}
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Название</th>
              <th className="px-4 py-3">Статус</th>
              <th className="px-4 py-3">Тип</th>
              <th className="px-4 py-3">Начало</th>
              <th className="px-4 py-3">Конец</th>
              <th className="px-4 py-3">Участники</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableSkeleton />
            ) : data?.results.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-16 text-center text-gray-500">
                  Соревнования не найдены
                </td>
              </tr>
            ) : (
              data?.results.map((contest, index) => {
                const rowNumber = (page - 1) * PAGE_SIZE + index + 1;
                return (
                  <tr key={contest.id} className="border-b border-gray-100 hover:bg-slate-50">
                    <td className="px-4 py-3 text-gray-400">{rowNumber}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">
                      <Link to={`/contests/${contest.id}`} className="hover:text-indigo-600">
                        {contest.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={contest.status} />
                    </td>
                    <td className="px-4 py-3">
                      <TypeBadge type={contest.type} />
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {format(new Date(contest.start_time), 'dd MMM yyyy, HH:mm', { locale: ru })}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {format(new Date(contest.end_time), 'dd MMM yyyy, HH:mm', { locale: ru })}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{contest.participant_count}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {!isLoading && data && data.count > 0 && (
        <div className="mt-6 flex items-center justify-center gap-4 text-sm text-gray-600">
          <button
            type="button"
            disabled={page <= 1 || isFetching}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 font-medium hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ← Назад
          </button>
          <span>
            Страница {page} из {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages || isFetching}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 font-medium hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Вперёд →
          </button>
        </div>
      )}
    </div>
  );
}
