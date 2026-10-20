/**
 * The Declare Incident, Update Status and Resolve Incident controls used to be buttons with no action.
 * They now call the existing POST /admin/incidents and PATCH /admin/incidents/{id} routes.
 */
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import IncidentsPage from '@/app/(protected)/incidents/page';
import IncidentDetailPage from '@/app/(protected)/incidents/detail/page';
import { fetchApi } from '@/lib/api';

const mockPush = jest.fn();
let mockCan: (permission: string) => boolean = () => true;

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams('id=inc-1'),
  useRouter: () => ({ push: mockPush }),
}));
jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ can: (permission: string) => mockCan(permission) }),
}));
jest.mock('@/components/ui/toast', () => ({ toast: { add: jest.fn() } }));
jest.mock('@/components/ui/data-table', () => ({
  DataTable: () => <div data-testid="data-table" />,
}));

const mockedFetchApi = jest.mocked(fetchApi);

const renderWithClient = (ui: React.ReactElement) =>
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      {ui}
    </QueryClientProvider>
  );

const incidentDetail = (status: string) => ({
  status: 'ok',
  incident: {
    id: 'inc-1',
    title: 'Worker down',
    severity: 'SEV-2',
    status,
    affected_service: 'worker',
    started_at: '2026-10-20T08:00:00Z',
    resolved_at: null,
    summary: 'The worker stopped',
    resolution: null,
  },
  events: [],
});

const configureDetail = (status: string) => {
  mockedFetchApi.mockImplementation((url, options) => {
    if (options && (options as { method?: string }).method === 'PATCH') return Promise.resolve({ status: 'ok' });
    return Promise.resolve(incidentDetail(status));
  });
};

const patchCalls = () =>
  mockedFetchApi.mock.calls.filter(([, options]) => (options as { method?: string } | undefined)?.method === 'PATCH');

beforeEach(() => {
  mockedFetchApi.mockReset();
  mockPush.mockReset();
  mockCan = () => true;
});

describe('Declare Incident (list page)', () => {
  const configureList = () =>
    mockedFetchApi.mockImplementation((url, options) => {
      if (options && (options as { method?: string }).method === 'POST') {
        return Promise.resolve({ status: 'ok', incident_id: 'new-incident' });
      }
      return Promise.resolve({ items: [], total: 0, page: 1, limit: 25 });
    });

  it('opens a form and posts the new incident', async () => {
    configureList();
    renderWithClient(<IncidentsPage />);
    fireEvent.click(await screen.findByRole('button', { name: /declare incident/i }));
    fireEvent.change(await screen.findByLabelText('Title'), { target: { value: 'Reports stuck' } });
    fireEvent.change(screen.getByLabelText('Severity'), { target: { value: 'SEV-1' } });
    fireEvent.change(screen.getByLabelText(/Affected service/), { target: { value: 'worker' } });
    fireEvent.click(screen.getByRole('button', { name: 'Declare incident' }));

    await waitFor(() => {
      expect(mockedFetchApi).toHaveBeenCalledWith('/api/v1/admin/incidents', {
        method: 'POST',
        data: { title: 'Reports stuck', severity: 'SEV-1', affected_service: 'worker', summary: null },
      });
    });
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/incidents/detail?id=new-incident'));
  });

  it('will not submit without a title', async () => {
    configureList();
    renderWithClient(<IncidentsPage />);
    fireEvent.click(await screen.findByRole('button', { name: /declare incident/i }));
    expect(await screen.findByRole('button', { name: 'Declare incident' })).toBeDisabled();
  });

  it('hides the button from admins who cannot manage incidents', async () => {
    mockCan = (permission) => permission !== 'incidents.manage';
    configureList();
    renderWithClient(<IncidentsPage />);
    await screen.findByText('Incident Log');
    expect(screen.queryByRole('button', { name: /declare incident/i })).toBeNull();
  });
});

describe('Incident detail actions', () => {
  it('resolves an incident with a resolution note', async () => {
    configureDetail('investigating');
    renderWithClient(<IncidentDetailPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Resolve Incident' }));
    fireEvent.change(await screen.findByLabelText(/Resolution/), { target: { value: 'Restarted the worker' } });
    fireEvent.click(screen.getByRole('button', { name: 'Resolve incident' }));

    await waitFor(() => expect(patchCalls()).toHaveLength(1));
    expect(patchCalls()[0]).toEqual([
      '/api/v1/admin/incidents/inc-1',
      { method: 'PATCH', data: { status: 'resolved', resolution: 'Restarted the worker' } },
    ]);
  });

  it('changes the status with an optional note', async () => {
    configureDetail('open');
    renderWithClient(<IncidentDetailPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Update Status' }));
    fireEvent.change(await screen.findByLabelText('New status'), { target: { value: 'identified' } });
    fireEvent.change(screen.getByLabelText(/Note/), { target: { value: 'Found the cause' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(patchCalls()).toHaveLength(1));
    expect(patchCalls()[0][1]).toEqual({ method: 'PATCH', data: { status: 'identified', message: 'Found the cause' } });
  });

  it('does not offer Resolve for an incident that is already resolved', async () => {
    configureDetail('resolved');
    renderWithClient(<IncidentDetailPage />);
    await screen.findByRole('button', { name: 'Update Status' });
    expect(screen.queryByRole('button', { name: 'Resolve Incident' })).toBeNull();
  });

  it('hides both buttons from admins who cannot manage incidents', async () => {
    mockCan = (permission) => permission !== 'incidents.manage';
    configureDetail('open');
    renderWithClient(<IncidentDetailPage />);
    await screen.findByText('Worker down');
    expect(screen.queryByRole('button', { name: 'Update Status' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Resolve Incident' })).toBeNull();
  });
});
