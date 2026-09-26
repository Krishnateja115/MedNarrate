import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Topbar } from '@/components/layout/topbar';

jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));

const mockPush = jest.fn();
let mockPathname = '/';
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => mockPathname,
}));

const mockCan = jest.fn();
const mockAuth = {
  user: {
    id: 'admin-1',
    email: 'admin@test.com',
    full_name: 'Test Admin',
    role: 'admin',
    permissions: ['security.view'],
  } as Record<string, unknown> | null,
  isAuthenticated: true,
  isLoading: false,
  authState: 'authenticated',
  can: mockCan,
  logout: jest.fn(),
};

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuth,
}));

const mockedFetchApi = jest.mocked(fetchApi);
const emptyAlertsResponse = { alerts: [], unread_count: 0 };
const alertsWithData = {
  alerts: [{
    id: 'alert-1',
    category: 'security',
    severity: 'critical',
    title: 'Suspicious access detected',
    message: 'A denied administrative access event requires review.',
    target_url: '/security',
    timestamp: '2026-09-26T03:00:00Z',
    acknowledged: false,
  }],
  unread_count: 1,
};

function makeClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
}

function renderTopbar() {
  return render(
    <QueryClientProvider client={makeClient()}>
      <Topbar />
    </QueryClientProvider>,
  );
}

describe('Topbar authentication and operations', () => {
  beforeEach(() => {
    mockedFetchApi.mockReset();
    mockPush.mockReset();
    mockCan.mockReset();
    mockCan.mockImplementation((permission) => permission === 'security.view');
    Object.assign(mockAuth, {
      user: {
        id: 'admin-1',
        email: 'admin@test.com',
        full_name: 'Test Admin',
        role: 'admin',
        permissions: ['security.view'],
      },
      isAuthenticated: true,
      isLoading: false,
      authState: 'authenticated',
    });
    mockPathname = '/';
    mockedFetchApi.mockImplementation((url) => {
      const endpoint = String(url);
      if (endpoint.includes('/alerts')) return Promise.resolve(emptyAlertsResponse);
      if (endpoint.includes('/break-glass/summary')) {
        return Promise.resolve({ status: 'ok', active_count: 0 });
      }
      return Promise.resolve({});
    });
  });

  it('waits for authentication initialization before calling protected APIs', () => {
    Object.assign(mockAuth, {
      user: null,
      isAuthenticated: false,
      isLoading: true,
      authState: 'initializing',
    });
    renderTopbar();
    expect(mockedFetchApi).not.toHaveBeenCalled();
    expect(screen.getByTitle('System alerts')).toBeDisabled();
  });

  it('does not call protected APIs when unauthenticated', () => {
    Object.assign(mockAuth, {
      user: null,
      isAuthenticated: false,
      isLoading: false,
      authState: 'unauthenticated',
    });
    renderTopbar();
    expect(mockedFetchApi).not.toHaveBeenCalled();
    expect(screen.getByTitle('System alerts')).toBeDisabled();
  });

  it('loads shared alerts and only the safe break-glass summary when authenticated', async () => {
    renderTopbar();
    await waitFor(() => {
      expect(mockedFetchApi).toHaveBeenCalledWith('/api/v1/admin/alerts');
      expect(mockedFetchApi).toHaveBeenCalledWith('/api/v1/admin/break-glass/summary');
    });
    expect(
      mockedFetchApi.mock.calls.some(([url]) => String(url).includes('/break-glass/grants')),
    ).toBe(false);
    expect(screen.getByText('Test Admin')).toBeInTheDocument();
  });

  it('does not request break-glass status without an eligible permission', async () => {
    mockCan.mockReturnValue(false);
    renderTopbar();
    await waitFor(() => expect(mockedFetchApi).toHaveBeenCalledWith('/api/v1/admin/alerts'));
    expect(
      mockedFetchApi.mock.calls.some(([url]) => String(url).includes('/break-glass')),
    ).toBe(false);
  });

  it('turns alerts into navigable operational actions', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if (String(url).includes('/alerts')) return Promise.resolve(alertsWithData);
      return Promise.resolve({ status: 'ok', active_count: 0 });
    });
    renderTopbar();
    await waitFor(() => expect(screen.getByText('Critical attention')).toBeInTheDocument());
    fireEvent.click(screen.getByTitle('System alerts'));
    fireEvent.click(screen.getByRole('button', { name: 'View →' }));
    expect(mockPush).toHaveBeenCalledWith('/security');
  });

  it('shows an explicit forbidden state for alert 403 responses', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if (String(url).includes('/alerts')) {
        return Promise.reject(Object.assign(new Error('Forbidden'), { status: 403 }));
      }
      return Promise.resolve({ status: 'ok', active_count: 0 });
    });
    renderTopbar();
    await waitFor(() => expect(screen.getByText('Status unavailable')).toBeInTheDocument());
    fireEvent.click(screen.getByTitle('System alerts'));
    expect(screen.getByText(/do not have permission/i)).toBeInTheDocument();
  });

  it('keeps controls stable during a network failure', async () => {
    mockedFetchApi.mockRejectedValue(Object.assign(new Error('Network error'), { status: 0 }));
    renderTopbar();
    await waitFor(() => expect(screen.getByText('Status unavailable')).toBeInTheDocument());
    fireEvent.click(screen.getByTitle('System alerts'));
    expect(screen.getByText(/temporarily unavailable/i)).toBeInTheDocument();
    expect(screen.getByText('Test Admin')).toBeInTheDocument();
  });

  it.each([
    ['Dashboard', '/'],
    ['Users', '/users'],
    ['Reports', '/reports'],
    ['Security', '/security'],
    ['Chat Ops', '/chat-ops'],
    ['RAG Ops', '/rag-ops'],
  ])('remains stable on %s navigation', (_page, pathname) => {
    mockPathname = pathname;
    const view = renderTopbar();
    expect(screen.getByPlaceholderText(/Search users/i)).toBeInTheDocument();
    expect(screen.getByTitle('Log out')).toBeInTheDocument();
    view.unmount();
  });
});
