import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';

import { inviteToContest } from '../api/contestsApi';

export default function InviteContestPage() {
  const { id } = useParams<{ id: string }>();
  const contestId = Number(id);
  const [handle, setHandle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim()) return;
    setIsSubmitting(true);
    try {
      await inviteToContest(contestId, handle.trim());
      toast.success(`Приглашение отправлено: ${handle}`);
      setHandle('');
    } catch {
      toast.error('Не удалось отправить приглашение');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-8 sm:px-6">
      <Link to={`/contests/${contestId}`} className="text-sm text-indigo-600 hover:text-indigo-800">
        ← Назад к соревнованию
      </Link>
      <h1 className="mt-4 mb-6 text-2xl font-bold text-gray-900">Пригласить участника</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Handle пользователя</label>
          <input
            type="text"
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            placeholder="username"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            required
          />
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Отправка…' : 'Пригласить'}
        </button>
      </form>
    </div>
  );
}
