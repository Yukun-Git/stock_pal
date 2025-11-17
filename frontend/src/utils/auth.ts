/**
 * Authentication utility functions for token management
 */

const AUTH_TOKEN_KEY = 'auth_token';
const AUTH_USER_KEY = 'auth_user';

export interface User {
  id: string;
  username: string;
  nickname?: string;
  email?: string;
  created_at?: string;
  last_login_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

/**
 * Store authentication token in localStorage
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
};

/**
 * Get authentication token from localStorage
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem(AUTH_TOKEN_KEY);
};

/**
 * Remove authentication token from localStorage
 */
export const removeAuthToken = (): void => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
};

/**
 * Check if user is authenticated (has valid token)
 */
export const isAuthenticated = (): boolean => {
  return !!getAuthToken();
};

/**
 * Store user information in localStorage
 */
export const setUser = (user: User): void => {
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
};

/**
 * Get user information from localStorage
 */
export const getUser = (): User | null => {
  const userStr = localStorage.getItem(AUTH_USER_KEY);
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch (error) {
    console.error('Failed to parse user data:', error);
    return null;
  }
};

/**
 * Remove user information from localStorage
 */
export const removeUser = (): void => {
  localStorage.removeItem(AUTH_USER_KEY);
};

/**
 * Clear all authentication data
 */
export const clearAuth = (): void => {
  removeAuthToken();
  removeUser();
};

/**
 * Get authorization header for API requests
 */
export const getAuthHeader = (): Record<string, string> | null => {
  const token = getAuthToken();
  if (!token) return null;

  return {
    'Authorization': `Bearer ${token}`,
  };
};
