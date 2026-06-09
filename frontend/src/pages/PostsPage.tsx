import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

import { getPosts } from '../api/postsApi';

const PAGE_SIZE = 20;

function TableSkeleton() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <tr key={i} className="animate-pulse border-b border-gray-100">
          <td className="px-4 py-4"><div className="h-4 w-64 rounded bg-gray-200" /></td>
          <td className="px-4 py-4"><div className="h-4 w-24 rounded bg-gray-200" /></td>
          <td className="px-4 py-4"><div className="h-4 w-32 rounded bg-gray-200" /></td>
        </tr>
      ))}
    </>
  );
}

export default function PostsPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['posts', page],
    queryFn: () => getPosts({ page }).then((res) => res.data),
    placeholderData: keepPreviousData,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Посты</h1>
          {data && (
            <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-sm font-medium text-indigo-700">
              {data.count}
            </span>
          )}
        </div>
        <Link
          to="/posts/create"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Написать
        </Link>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Название</th>
              <th className="px-4 py-3">Автор</th>
              <th className="px-4 py-3">Дата</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableSkeleton />
            ) : data?.results.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-16 text-center text-gray-500">
                  Постов пока нет
                </td>
              </tr>
            ) : (
              data?.results.map((post) => (
                <tr key={post.id} className="border-b border-gray-100 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link to={`/posts/${post.id}`} className="font-medium text-gray-900 hover:text-indigo-600">
                      {post.title}
                    </Link>
                    <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">{post.excerpt}</p>
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/profile/${post.author.handle}`} className="text-indigo-600 hover:text-indigo-800">
                      {post.author.handle}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {format(new Date(post.created_at), 'dd MMM yyyy', { locale: ru })}
                  </td>
                </tr>
              ))
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
