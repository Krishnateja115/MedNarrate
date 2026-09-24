/* eslint-disable */
'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { fetchApi } from '@/lib/api';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  permissions?: string[];
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
  can: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const logout = useCallback(async () => {
    const refreshToken = sessionStorage.getItem('admin_refresh_token');
    
    // Attempt backend logout if we have a refresh token
    if (refreshToken) {
      try {
        await fetchApi('/api/v1/auth/logout', {
          method: 'POST',
          data: { refresh_token: refreshToken },
        });
      } catch (err) {
        console.error('Logout request failed', err);
      }
    }

    sessionStorage.removeItem('admin_token');
    sessionStorage.removeItem('admin_refresh_token');
    sessionStorage.removeItem('admin_user');
    setToken(null);
    setUser(null);
    router.push('/login');
  }, [router]);

  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [logout]);

  useEffect(() => {
    const storedToken = sessionStorage.getItem('admin_token');
    const storedUser = sessionStorage.getItem('admin_user');

    if (storedToken && storedUser) {
      setToken(storedToken);
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        logout();
      }
    } else if (pathname !== '/login') {
      router.push('/login');
    }
    
    setIsLoading(false);
  }, [pathname, router, logout]);

  const login = (newToken: string, newRefreshToken: string, newUser: User) => {
    sessionStorage.setItem('admin_token', newToken);
    sessionStorage.setItem('admin_refresh_token', newRefreshToken);
    sessionStorage.setItem('admin_user', JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
    router.push('/');
  };

  const can = useCallback((permission: string) => {
    if (!user || !user.permissions) return false;
    if (user.permissions.includes('super_admin') || user.permissions.includes('Super Admin')) return true;
    return user.permissions.includes(permission);
  }, [user]);

  const hasAnyPermission = useCallback((permissions: string[]) => {
    if (!user || !user.permissions) return false;
    if (user.permissions.includes('super_admin') || user.permissions.includes('Super Admin')) return true;
    return permissions.some(p => user.permissions!.includes(p));
  }, [user]);

  const hasAllPermissions = useCallback((permissions: string[]) => {
    if (!user || !user.permissions) return false;
    if (user.permissions.includes('super_admin') || user.permissions.includes('Super Admin')) return true;
    return permissions.every(p => user.permissions!.includes(p));
  }, [user]);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, isLoading, login, logout, can, hasAnyPermission, hasAllPermissions }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
