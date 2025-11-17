import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';
import {
  User,
  LoginResponse,
  getAuthToken,
  setAuthToken,
  removeAuthToken,
  getUser,
  setUser,
  removeUser,
  clearAuth,
} from '@/utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUserState] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken();
      const savedUser = getUser();

      if (token && savedUser) {
        setUserState(savedUser);

        // Optionally refresh user data from server
        try {
          await refreshUser();
        } catch (error) {
          console.error('Failed to refresh user data:', error);
          // If refresh fails, still use cached user data
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  /**
   * Login with username and password
   */
  const login = async (username: string, password: string): Promise<void> => {
    try {
      const response = await axios.post<LoginResponse>(
        `${API_BASE_URL}/api/v1/auth/login`,
        { username, password }
      );

      const { access_token, user: userData } = response.data;

      // Store token and user data
      setAuthToken(access_token);
      setUser(userData);
      setUserState(userData);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  /**
   * Logout and clear auth data
   */
  const logout = (): void => {
    // Optionally call logout API
    const token = getAuthToken();
    if (token) {
      axios.post(`${API_BASE_URL}/api/v1/auth/logout`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }).catch(error => {
        console.error('Logout API call failed:', error);
      });
    }

    // Clear local auth data
    clearAuth();
    setUserState(null);
  };

  /**
   * Refresh user data from server
   */
  const refreshUser = async (): Promise<void> => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No auth token found');
    }

    try {
      const response = await axios.get<User>(
        `${API_BASE_URL}/api/v1/auth/me`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      const userData = response.data;
      setUser(userData);
      setUserState(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh fails with 401, clear auth
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        clearAuth();
        setUserState(null);
      }
      throw error;
    }
  };

  const value: AuthContextValue = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to use auth context
 */
export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
