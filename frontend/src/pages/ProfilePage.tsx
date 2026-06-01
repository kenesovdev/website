import { useParams } from 'react-router-dom';

export default function ProfilePage() {
  const { handle } = useParams<{ handle: string }>();

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <h1 className="text-2xl font-bold text-gray-900">Профиль: {handle}</h1>
      <p className="mt-2 text-gray-500">Phase 2.6 — профиль пользователя</p>
    </div>
  );
}
