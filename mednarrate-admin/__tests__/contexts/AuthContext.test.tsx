import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import * as api from '@/lib/api';

// Mock Next.js navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/login',
}));

// Mock API
jest.mock('@/lib/api', () => {
  return {
    __esModule: true,
    ...jest.requireActual('@/lib/api'),
    fetchApi: jest.fn(),
  };
});

const TestComponent = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  if (isLoading) return <div>Loading...</div>;
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'Authenticated' : 'Unauthenticated'}</div>
      {user && <div data-testid="user-email">{user.email}</div>}
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('handles initial unauthenticated bootstrap without throwing', async () => {
    (api.fetchApi as jest.Mock).mockRejectedValueOnce({ status: 401, message: 'Unauthorized' });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Unauthenticated');
    });

    // Should NOT redirect to login if we are already on /login (handled by mock)
    expect(mockPush).not.toHaveBeenCalled();
    // fetchApi should have been called with suppressAuthError
    expect(api.fetchApi).toHaveBeenCalledWith('/api/v1/admin/me', { suppressAuthError: true });
  });

  test('handles valid authenticated bootstrap', async () => {
    (api.fetchApi as jest.Mock).mockResolvedValueOnce({
      id: '1',
      email: 'admin@mednarrate.com',
      full_name: 'Admin',
      role: 'admin',
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('admin@mednarrate.com');
    });
  });

  test('handles logout', async () => {
    (api.fetchApi as jest.Mock)
      .mockResolvedValueOnce({
        id: '1',
        email: 'admin@mednarrate.com',
        full_name: 'Admin',
        role: 'admin',
      }) // fetchUser
      .mockResolvedValueOnce({}); // logout api

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });

    act(() => {
      screen.getByText('Logout').click();
    });

    await waitFor(() => {
      expect(api.fetchApi).toHaveBeenCalledWith('/api/v1/auth/logout', expect.any(Object));
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Unauthenticated');
    });
  });

  test('handles network failure gracefully', async () => {
    (api.fetchApi as jest.Mock).mockRejectedValueOnce({ status: 0, message: 'Network error' });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Unauthenticated');
    });
  });
});
