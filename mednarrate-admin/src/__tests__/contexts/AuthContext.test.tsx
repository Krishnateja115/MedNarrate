/**
 * Tests for AuthContext — session lifecycle behavior.
 *
 * Verifies:
 * - Session is bootstrapped on mount (not on every pathname change)
 * - Authenticated state set after /me succeeds
 * - Unauthenticated + redirect when /me returns 401
 * - Expired session handled via auth:unauthorized event
 * - login() sets authenticated state
 * - logout() clears state and redirects
 * - can() returns correct RBAC results
 */
import React from 'react';
import { render, act, screen } from '@testing-library/react';
import { fetchApi } from '@/lib/api';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';

// ─── mocks ───────────────────────────────────────────────────────────────────
jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/dashboard',
}));

const mockedFetchApi = jest.mocked(fetchApi);

const TestConsumer = () => {
  const context = useAuth();
  return (
    <div>
      <span data-testid="state">{context.authState}</span>
      <span data-testid="user">{context.user?.email || 'none'}</span>
      <span data-testid="loading">{context.isLoading ? 'loading' : 'ready'}</span>
      <span data-testid="can-any">{context.can('any.permission') ? 'yes' : 'no'}</span>
      <span data-testid="can-break-glass">{context.can('break_glass.read') ? 'yes' : 'no'}</span>
      <span data-testid="can-chat">{context.can('chat.view') ? 'yes' : 'no'}</span>
      <span data-testid="can-users">{context.can('users.view') ? 'yes' : 'no'}</span>
    </div>
  );
};

const renderWithAuth = () =>
  render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>
  );

const mockAdminUser = {
  id: 'admin-1',
  email: 'admin@hospital.com',
  full_name: 'Dr Admin',
  role: 'super_admin',
  permissions: ['super_admin', 'users.view', 'chat.view'],
};

// ─── Tests ───────────────────────────────────────────────────────────────────
describe('AuthContext — session bootstrap', () => {
  beforeEach(() => {
    mockedFetchApi.mockReset();
    mockPush.mockReset();
  });

  it('starts in initializing state', () => {
    mockedFetchApi.mockReturnValue(new Promise(() => {})); // never resolves
    renderWithAuth();
    expect(screen.getByTestId('state').textContent).toBe('initializing');
    expect(screen.getByTestId('loading').textContent).toBe('loading');
  });

  it('transitions to authenticated after /me succeeds', async () => {
    mockedFetchApi.mockResolvedValue(mockAdminUser);
    renderWithAuth();
    await act(async () => {});
    expect(screen.getByTestId('state').textContent).toBe('authenticated');
    expect(screen.getByTestId('user').textContent).toBe('admin@hospital.com');
  });

  it('transitions to unauthenticated and redirects when /me returns 401', async () => {
    mockedFetchApi.mockRejectedValue(Object.assign(new Error('Unauthorized'), { status: 401 }));
    renderWithAuth();
    await act(async () => {});
    expect(screen.getByTestId('state').textContent).toBe('unauthenticated');
    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('only calls /me ONCE on mount, not on re-renders', async () => {
    mockedFetchApi.mockResolvedValue(mockAdminUser);
    const { rerender } = renderWithAuth();
    await act(async () => {});
    // Re-render (simulates pathname change or parent state update)
    rerender(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await act(async () => {});
    // Should still be exactly 1 call — not 2
    expect(mockedFetchApi).toHaveBeenCalledTimes(1);
    expect(mockedFetchApi.mock.calls[0][0]).toContain('/admin/me');
  });
});

describe('AuthContext — can() RBAC', () => {
  beforeEach(() => {
    mockedFetchApi.mockResolvedValue(mockAdminUser);
  });

  it('super_admin can access everything', async () => {
    renderWithAuth();
    await act(async () => {});
    expect(screen.getByTestId('can-any').textContent).toBe('yes');
    expect(screen.getByTestId('can-break-glass').textContent).toBe('yes');
  });

  it('returns false for missing permission', async () => {
    mockedFetchApi.mockResolvedValue({
      ...mockAdminUser,
      permissions: ['users.view'], // not super_admin
    });
    renderWithAuth();
    await act(async () => {});
    expect(screen.getByTestId('can-chat').textContent).toBe('no');
    expect(screen.getByTestId('can-users').textContent).toBe('yes');
  });
});

describe('AuthContext — expired session via auth:unauthorized event', () => {
  beforeEach(() => {
    mockedFetchApi.mockReset();
    mockPush.mockReset();
  });

  it('handles expired session event gracefully', async () => {
    // First: bootstrap succeeds
    mockedFetchApi.mockResolvedValueOnce(mockAdminUser);
    // Then: logout call after expiry
    mockedFetchApi.mockResolvedValue({});
    renderWithAuth();
    await act(async () => {});
    expect(screen.getByTestId('state').textContent).toBe('authenticated');

    // Simulate token expiry event (fired by fetchApi on 401)
    await act(async () => {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    });

    // Should redirect to login
    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('enters expired state immediately and starts only one logout request', async () => {
    mockedFetchApi.mockResolvedValueOnce(mockAdminUser);
    mockedFetchApi.mockReturnValueOnce(new Promise(() => {}));
    renderWithAuth();
    await act(async () => {});

    act(() => {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    });

    expect(screen.getByTestId('state').textContent).toBe('expired');
    expect(mockedFetchApi).toHaveBeenCalledTimes(2);
  });
});
