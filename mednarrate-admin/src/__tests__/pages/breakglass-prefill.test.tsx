import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import BreakGlassPage from '@/app/(protected)/breakglass/page';

jest.mock('next/navigation', () => ({ useSearchParams: () => new URLSearchParams('resource_type=chat_session&resource_id=35e3b69e-ccbe-4b88-8d75-130921041831') }));
jest.mock('@/lib/api', () => ({ fetchApi: jest.fn().mockResolvedValue({ grants: [] }) }));
jest.mock('@/contexts/AuthContext', () => ({ useAuth: () => ({ user: { id: 'admin-1' }, can: () => true, hasAnyPermission: () => false }) }));
jest.mock('@/components/step-up-dialog', () => ({ useStepUp: () => ({ requestStepUp: jest.fn(), stepUpDialog: null }), STEP_UP_CANCELLED: 'cancelled' }));

it('opens the request form with the chat session ID and type filled in', () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><BreakGlassPage /></QueryClientProvider>);
  expect(screen.getByText('Emergency Sensitive Access Request Form')).toBeInTheDocument();
  expect(screen.getByDisplayValue('35e3b69e-ccbe-4b88-8d75-130921041831')).toBeInTheDocument();
  expect(screen.getByDisplayValue('Chat Session')).toBeInTheDocument();
  expect(screen.getByPlaceholderText('Enter detailed reason for emergency access...')).toHaveValue('');
});
