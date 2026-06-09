import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Link, useNavigate, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import toast from 'react-hot-toast';

import { deletePost, getPost } from '../api/postsApi';
import FullPageSpinner from '../components/FullPageSpinner';
import { useAuthStore } from '../store/authStore';

export default function PostDetailPage() {
  const { id } = useParams<{ id: string }>();
  const postId = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const { data: post, isLoading } = useQuery({
    queryKey: ['post', postId],
    queryFn: () => getPost(postId).then((res) => res.data),
    enabled: Number.isFinite(postId),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deletePost(postId),
    onSuccess: () => {
      toast.success('Пост удалён');
      queryClient.invalidateQueries({ queryKey: ['posts'] });
      navigate('/posts');
    },
    onError: () => toast.error('Не удалось удалить пост'),
  });

  if (isLoading || !post) {
    return <FullPageSpinner />;
  }

  const canEdit = user && (user.id === post.author.id || user.role === 'admin');

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <Link to="/posts" className="text-sm text-indigo-600 hover:text-indigo-800">
        ← Все посты
      </Link>

      <article className="mt-4">
        <h1 className="text-3xl font-bold text-gray-900">{post.title}</h1>
        <p className="mt-2 text-sm text-gray-500">
          <Link to={`/profile/${post.author.handle}`} className="text-indigo-600 hover:text-indigo-800">
            {post.author.handle}
          </Link>
          {' · '}
          {format(new Date(post.created_at), 'dd MMMM yyyy, HH:mm', { locale: ru })}
        </p>

        {canEdit && (
          <div className="mt-4 flex gap-2">
            <Link
              to={`/posts/${post.id}/edit`}
              className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Редактировать
            </Link>
            <button
              type="button"
              onClick={() => {
                if (window.confirm('Удалить пост?')) {
                  deleteMutation.mutate();
                }
              }}
              disabled={deleteMutation.isPending}
              className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-100 disabled:opacity-50"
            >
              Удалить
            </button>
          </div>
        )}

        <div className="prose prose-sm mt-8 max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{post.content}</ReactMarkdown>
        </div>
      </article>
    </div>
  );
}
