import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AdminManagementPage from '@/app/(protected)/admins/page';
import { fetchApi } from '@/lib/api';

jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));

let canManage = true;
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'current-admin', email: 'current@example.com' },
    can: () => canManage,
  }),
}));

const mockedFetchApi = jest.mocked(fetchApi);

const activeAdmin = {
  id: 'active-admin',
  email: 'active@example.com',
  full_name: 'Active Admin',
  role: 'admin',
  is_active: true,
  is_super_admin: false,
  created_at: null,
  last_login_at: null,
  roles: [],
  active_sessions: 2,
};

const inactiveAdmin = {
  ...activeAdmin,
  id: 'inactive-admin',
  email: 'inactive@example.com',
  full_name: 'Inactive Admin',
  is_active: false,
  active_sessions: 0,
};

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const invalidate = jest.spyOn(client, 'invalidateQueries');
  render(
    <QueryClientProvider client={client}>
      <AdminManagementPage />
    </QueryClientProvider>
  );
  return { invalidate };
}

describe('Admin Accounts controls', () => {
  beforeEach(() => {
    canManage = true;
    mockedFetchApi.mockReset();
    mockedFetchApi.mockImplementation((url) => {
      if (String(url) === '/api/v1/admin/admins') {
        return Promise.resolve({ admins: [activeAdmin, inactiveAdmin] });
      }
      return Promise.resolve({ status: 'ok' });
    });
    jest.spyOn(window, 'confirm').mockReturnValue(true);
  });

  afterEach(() => jest.restoreAllMocks());

  it('maps the current active state to deactivate and refreshes the list', async () => {
    const { invalidate } = renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Deactivate' }));

    await waitFor(() =>
      expect(mockedFetchApi).toHaveBeenCalledWith(
        '/api/v1/admin/admins/active-admin/deactivate',
        { method: 'POST' }
      )
    );
    expect(window.confirm).toHaveBeenCalledWith(
      expect.stringContaining('Active sessions will be revoked')
    );
    await waitFor(() =>
      expect(invalidate).toHaveBeenCalledWith({ queryKey: ['admin-users'] })
    );
  });

  it('maps the current inactive state to reactivate', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Reactivate' }));
    await waitFor(() =>
      expect(mockedFetchApi).toHaveBeenCalledWith(
        '/api/v1/admin/admins/inactive-admin/reactivate',
        { method: 'POST' }
      )
    );
  });

  it('does not mutate when confirmation is cancelled', async () => {
    jest.mocked(window.confirm).mockReturnValue(false);
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Deactivate' }));
    expect(mockedFetchApi).not.toHaveBeenCalledWith(
      expect.stringContaining('/deactivate'),
      expect.anything()
    );
  });

  it('renders a mutation failure without losing the account table', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if (String(url) === '/api/v1/admin/admins') {
        return Promise.resolve({ admins: [activeAdmin] });
      }
      return Promise.reject(new Error('Hierarchy rule blocked this action'));
    });
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Deactivate' }));
    expect(await screen.findByText('Hierarchy rule blocked this action')).toBeInTheDocument();
    expect(screen.getByText('active@example.com')).toBeInTheDocument();
  });

  it('hides mutation controls without admins.manage', async () => {
    canManage = false;
    renderPage();
    expect(await screen.findByText('active@example.com')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Deactivate' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Create Admin Account/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Force Logout/ })).not.toBeInTheDocument();
  });
});
