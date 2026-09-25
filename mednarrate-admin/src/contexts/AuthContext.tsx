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
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User) => void;
  logout: () => void;
  can: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const logout = useCallback(async () => {
    try {
      await fetchApi('/api/v1/auth/logout', {
        method: 'POST',
      });
    } catch (err) {
      console.error('Logout request failed', err);
    }
    setUser(null);
    if (pathname !== '/login') {
      router.push('/login');
    }
  }, [router, pathname]);

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
    let mounted = true;
    const fetchUser = async () => {
      try {
        const currentUser = await fetchApi('/api/v1/admin/me', { suppressAuthError: true });
        if (mounted) {
          setUser(currentUser);
        }
      } catch (err) {
        if (mounted) {
          setUser(null);
          if (pathname !== '/login') {
            router.push('/login');
          }
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    fetchUser();
    return () => { mounted = false; };
  }, [pathname, router]);

  const login = (newUser: User) => {
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
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, can, hasAnyPermission, hasAllPermissions }}>
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
