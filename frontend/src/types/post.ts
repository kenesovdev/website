export interface PostAuthor {
  id: string;
  handle: string;
}

export interface Post {
  id: number;
  title: string;
  excerpt: string;
  author: PostAuthor;
  published: boolean;
  created_at: string;
  updated_at: string;
}

export interface PostDetail extends Post {
  content: string;
}

export interface CreatePostPayload {
  title: string;
  content: string;
  published?: boolean;
}

export interface PaginatedPosts {
  count: number;
  next: string | null;
  previous: string | null;
  results: Post[];
}
