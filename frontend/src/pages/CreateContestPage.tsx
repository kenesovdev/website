import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

import { createContest } from '../api/contestsApi';
import { getProblems } from '../api/problemsApi';
import type { ContestParticipationType } from '../types/contest';

export default function CreateContestPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [participationType, setParticipationType] = useState<ContestParticipationType>('OPEN');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [selectedProblems, setSelectedProblems] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: problemsData } = useQuery({
    queryKey: ['problems-for-contest'],
    queryFn: () => getProblems({ page: 1 }).then((res) => res.data),
  });

  const toggleProblem = (id: string) => {
    setSelectedProblems((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !startTime || !endTime) {
      toast.error('Заполните обязательные поля');
      return;
    }
    setIsSubmitting(true);
    try {
      const { data } = await createContest({
        title,
        description,
        participation_type: participationType,
        start_time: new Date(startTime).toISOString(),
        end_time: new Date(endTime).toISOString(),
        is_public: participationType === 'OPEN',
        problems: selectedProblems.map((problem_id, order) => ({
          problem_id,
          order,
          order_label: String.fromCharCode(65 + order),
        })),
      });
      toast.success('Соревнование создано');
      navigate(`/contests/${data.id}`);
    } catch {
      toast.error('Не удалось создать соревнование');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Создать соревнование</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Название</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Описание</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Тип участия</label>
          <select
            value={participationType}
            onChange={(e) => setParticipationType(e.target.value as ContestParticipationType)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="OPEN">Открытое</option>
            <option value="INVITE_ONLY">По приглашению</option>
          </select>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Начало</label>
            <input
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Конец</label>
            <input
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              required
            />
          </div>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">Задачи</label>
          <div className="max-h-64 overflow-y-auto rounded-lg border border-gray-200">
            {problemsData?.results.map((problem) => (
              <label
                key={problem.slug}
                className="flex cursor-pointer items-center gap-3 border-b border-gray-100 px-4 py-3 hover:bg-gray-50 last:border-0"
              >
                <input
                  type="checkbox"
                  checked={selectedProblems.includes(problem.id)}
                  onChange={() => toggleProblem(problem.id)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-900">{problem.title}</span>
                <span className="ml-auto text-xs text-gray-500">{problem.difficulty}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Создание…' : 'Создать'}
        </button>
      </form>
    </div>
  );
}
