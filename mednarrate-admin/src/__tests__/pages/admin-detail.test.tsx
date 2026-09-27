import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AdminDetailPage from '@/app/(protected)/admins/detail/page';
import { fetchApi } from '@/lib/api';

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams('id=admin-1'),
}));
jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));

const mockedFetchApi = jest.mocked(fetchApi);

const renderPage = () =>
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <AdminDetailPage />
    </QueryClientProvider>
  );

const admin = {
  id: 'admin-1',
  email: 'admin@example.com',
  full_name: 'Support Admin',
  is_active: true,
  is_super_admin: false,
  roles: [],
  created_at: null,
  last_login_at: null,
};

const configureApi = (supportResponse: unknown = { status: 'ok', tickets: [] }) => {
  mockedFetchApi.mockImplementation((url) => {
    const path = String(url);
    if (path === '/api/v1/admin/admins/admin-1') return Promise.resolve(admin);
    if (path.endsWith('/support_tickets')) return Promise.resolve(supportResponse);
    if (path.endsWith('/audit_logs')) return Promise.resolve({ logs: [] });
    return Promise.resolve({});
  });
};

describe('Admin detail support tickets', () => {
  beforeEach(() => mockedFetchApi.mockReset());

  it('renders the canonical empty state', async () => {
    configureApi();
    renderPage();
    fireEvent.click(await screen.findByRole('tab', { name: 'Assigned Tickets' }));
    expect(await screen.findByText('No assigned tickets.')).toBeInTheDocument();
  });

  it('renders multiple assigned tickets', async () => {
    configureApi({
      status: 'ok',
      tickets: [
        { id: 'ticket-1', subject: 'Report stuck', priority: 'P2 High', status: 'New', created_at: '2026-09-27T00:00:00Z' },
        { id: 'ticket-2', subject: 'Login issue', priority: 'P3 Normal', status: 'Resolved', created_at: '2026-09-27T01:00:00Z' },
      ],
    });
    renderPage();
    fireEvent.click(await screen.findByRole('tab', { name: 'Assigned Tickets' }));
    expect(await screen.findByText('Report stuck')).toBeInTheDocument();
    expect(screen.getByText('Login issue')).toBeInTheDocument();
  });

  it('shows a bounded error and retries without crashing the page', async () => {
    let attempts = 0;
    mockedFetchApi.mockImplementation((url) => {
      const path = String(url);
      if (path === '/api/v1/admin/admins/admin-1') return Promise.resolve(admin);
      if (path.endsWith('/audit_logs')) return Promise.resolve({ logs: [] });
      if (path.endsWith('/support_tickets')) {
        attempts += 1;
        return attempts === 1
          ? Promise.reject(new Error('backend failure'))
          : Promise.resolve({ status: 'ok', tickets: [] });
      }
      return Promise.resolve({});
    });
    renderPage();
    fireEvent.click(await screen.findByRole('tab', { name: 'Assigned Tickets' }));
    expect(await screen.findByText('Failed to load assigned tickets.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    await waitFor(() => expect(screen.getByText('No assigned tickets.')).toBeInTheDocument());
    expect(attempts).toBe(2);
  });
});
