import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AIOperationsPage from '@/app/(protected)/ai-ops/page';
import { fetchApi } from '@/lib/api';

jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));
const mockedFetchApi = jest.mocked(fetchApi);

function renderPage() {
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <AIOperationsPage />
    </QueryClientProvider>
  );
}

describe('AI Operations failure states', () => {
  beforeEach(() => mockedFetchApi.mockReset());

  it('does not display fabricated zero metrics when the overview fails', async () => {
    mockedFetchApi.mockRejectedValue(new Error('offline'));
    renderPage();
    expect(await screen.findByText(/AI overview could not be loaded/)).toBeInTheDocument();
    expect(screen.queryByText('0%')).not.toBeInTheDocument();
  });

  it('shows bounded errors for traces and failure analysis', async () => {
    mockedFetchApi.mockRejectedValue(new Error('offline'));
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: 'Request Traces' }));
    expect(await screen.findByText('Request traces could not be loaded.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: 'Failure Analysis' }));
    expect(await screen.findByText('Failure analysis could not be loaded.')).toBeInTheDocument();
  });
});
