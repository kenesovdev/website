import type { CreatePostPayload, PaginatedPosts, PostDetail } from '../types/post';
import api from './axios';

export const getPosts = (params?: { page?: number }) =>
  api.get<PaginatedPosts>('/posts/', { params });

export const getPost = (id: number) =>
  api.get<PostDetail>(`/posts/${id}/`);

export const createPost = (payload: CreatePostPayload) =>
  api.post<PostDetail>('/posts/', payload);

export const updatePost = (id: number, payload: CreatePostPayload) =>
  api.put<PostDetail>(`/posts/${id}/`, payload);

export const deletePost = (id: number) =>
  api.delete(`/posts/${id}/`);
