import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import toast from 'react-hot-toast';

import { createPost } from '../api/postsApi';

type Tab = 'editor' | 'preview' | 'split';

export default function CreatePostPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tab, setTab] = useState<Tab>('split');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      toast.error('Заполните название и текст');
      return;
    }
    setIsSubmitting(true);
    try {
      const { data } = await createPost({ title, content, published: true });
      toast.success('Пост опубликован');
      navigate(`/posts/${data.id}`);
    } catch {
      toast.error('Не удалось создать пост');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Новый пост</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
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

        <div className="flex gap-2 border-b border-gray-200">
          {(['editor', 'preview', 'split'] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`px-3 py-2 text-sm font-medium ${
                tab === t
                  ? 'border-b-2 border-indigo-600 text-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t === 'editor' ? 'Редактор' : t === 'preview' ? 'Превью' : 'Разделённый'}
            </button>
          ))}
        </div>

        <div className={`grid gap-4 ${tab === 'split' ? 'md:grid-cols-2' : 'grid-cols-1'}`}>
          {(tab === 'editor' || tab === 'split') && (
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={16}
              placeholder="Markdown..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          )}
          {(tab === 'preview' || tab === 'split') && (
            <div className="prose prose-sm min-h-[16rem] max-w-none rounded-lg border border-gray-200 bg-gray-50 p-4">
              {content ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              ) : (
                <p className="text-gray-400">Превью появится здесь</p>
              )}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Публикация…' : 'Опубликовать'}
        </button>
      </form>
    </div>
  );
}
