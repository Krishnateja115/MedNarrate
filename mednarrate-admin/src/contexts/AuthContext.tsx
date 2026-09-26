'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { fetchApi } from '@/lib/api';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  permissions?: string[];
}

/** Auth lifecycle states. 'initializing' means we haven't confirmed session yet. */
type AuthState = 'initializing' | 'authenticated' | 'unauthenticated' | 'expired';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  /** True while the first session check hasn't resolved yet. */
  isLoading: boolean;
  authState: AuthState;
  login: (user: User) => void;
  logout: () => void;
  can: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const PUBLIC_PATHS = ['/login'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [authState, setAuthState] = useState<AuthState>('initializing');
  const router = useRouter();
  const pathname = usePathname();
  // Track whether the initial session check has ever completed
  const initializedRef = useRef(false);
  const expiryInProgressRef = useRef(false);

  const logout = useCallback(async (reason: 'manual' | 'expired' = 'manual') => {
    if (reason === 'expired' && expiryInProgressRef.current) return;
    if (reason === 'expired') expiryInProgressRef.current = true;
    if (reason === 'expired') {
      setAuthState('expired');
    }
    try {
      await fetchApi('/api/v1/auth/logout', { method: 'POST' });
    } catch {
      // Silent — logout should always clear local state
    }
    setUser(null);
    setAuthState('unauthenticated');
    if (!PUBLIC_PATHS.includes(pathname)) {
      router.push('/login');
    }
  }, [router, pathname]);

  // Listen for 401 events dispatched by fetchApi for protected calls
  useEffect(() => {
    const handleUnauthorized = () => {
      // Only trigger session expiry if we were previously authenticated
      // Avoids a cold-start 401 from /me being mistaken for session expiry
      if (authState === 'authenticated') {
        logout('expired');
      }
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [authState, logout]);

  // ONE-TIME session bootstrap on mount only.
  // Does NOT re-run on pathname changes — navigation must not re-validate the session.
  useEffect(() => {
    let mounted = true;

    const bootstrapSession = async () => {
      try {
        const currentUser = await fetchApi<User>('/api/v1/admin/me', {
          suppressAuthError: true,
        });
        if (mounted) {
          setUser(currentUser);
          setAuthState('authenticated');
        }
      } catch {
        if (mounted) {
          setUser(null);
          setAuthState('unauthenticated');
          if (!PUBLIC_PATHS.includes(pathname)) {
            router.push('/login');
          }
        }
      } finally {
        if (mounted) {
          initializedRef.current = true;
        }
      }
    };

    bootstrapSession();
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps: runs once on mount only

  // On pathname change, if we're already authenticated, do nothing.
  // If we're unauthenticated and navigating to a protected route, redirect.
  useEffect(() => {
    if (!initializedRef.current) return; // Still initializing — wait for bootstrap
    if (authState === 'unauthenticated' && !PUBLIC_PATHS.includes(pathname)) {
      router.push('/login');
    }
  }, [pathname, authState, router]);

  const login = useCallback((newUser: User) => {
    expiryInProgressRef.current = false;
    setUser(newUser);
    setAuthState('authenticated');
    router.push('/');
  }, [router]);

  const can = useCallback((permission: string) => {
    if (!user?.permissions) return false;
    if (user.permissions.includes('super_admin') || user.permissions.includes('Super Admin')) return true;
    return user.permissions.includes(permission);
  }, [user]);

  const hasAnyPermission = useCallback((permissions: string[]) => {
    if (!user?.permissions) return false;
    if (user.permissions.includes('super_admin') || user.permissions.includes('Super Admin')) return true;
    return permissions.some(p => user.permissions!.includes(p));
  }, [user]);

  const hasAllPermissions = useCallback((permissions: string[]) => {
    if (!user?.permissions) return false;
    if (user.permissions.includes('super_admin') || user.permissions.includes('Super Admin')) return true;
    return permissions.every(p => user.permissions!.includes(p));
  }, [user]);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: authState === 'authenticated',
      isLoading: authState === 'initializing',
      authState,
      login,
      logout: () => logout('manual'),
      can,
      hasAnyPermission,
      hasAllPermissions,
    }}>
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
