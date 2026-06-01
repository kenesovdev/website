export interface User {
  id: string;
  email: string;
  handle: string;
  role: 'user' | 'admin';
}

export interface AuthResponse {
  access_token: string;
  user: User;
}
