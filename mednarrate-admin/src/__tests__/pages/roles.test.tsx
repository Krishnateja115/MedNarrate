import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import RolesAndPermissionsPage from '@/app/(protected)/roles/page';
import { fetchApi } from '@/lib/api';

jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ can: () => true }),
}));

const mockedFetchApi = jest.mocked(fetchApi);

describe('Roles API contract', () => {
  beforeEach(() => {
    mockedFetchApi.mockReset();
    mockedFetchApi.mockImplementation((url) => {
      if (String(url) === '/api/v1/admin/roles') {
        return Promise.resolve([
          { id: 'role-1', name: 'Support', description: null, permissions: [] },
        ]);
      }
      if (String(url) === '/api/v1/admin/roles/permissions') {
        return Promise.resolve([
          { id: 'permission-1', name: 'support.view', description: 'View support' },
        ]);
      }
      return Promise.resolve({ status: 'ok' });
    });
  });

  it('updates permissions through the implemented role endpoint', async () => {
    render(
      <QueryClientProvider
        client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
      >
        <RolesAndPermissionsPage />
      </QueryClientProvider>
    );

    fireEvent.click(await screen.findByRole('checkbox'));
    await waitFor(() =>
      expect(mockedFetchApi).toHaveBeenCalledWith('/api/v1/admin/roles/role-1', {
        method: 'PUT',
        data: { permission_names: ['support.view'] },
      })
    );
  });
});
