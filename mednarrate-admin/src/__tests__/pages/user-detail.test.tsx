/**
 * User detail: the clinician / caregiver "Verify" buttons must call the real routes, and the profile
 * card must read the field names the backend actually sends.
 */
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import UserDetailPage from '@/app/(protected)/users/detail/page';
import { fetchApi } from '@/lib/api';

let mockCan: (permission: string) => boolean = () => true;

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams('id=user-1'),
}));
jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ can: (permission: string) => mockCan(permission) }),
}));
jest.mock('@/components/step-up-dialog', () => ({
  STEP_UP_CANCELLED: 'step-up-cancelled',
  useStepUp: () => ({ requestStepUp: jest.fn(), stepUpDialog: null }),
}));

const mockedFetchApi = jest.mocked(fetchApi);

const user = {
  id: 'user-1',
  email: 'clinician@example.com',
  full_name: 'Dr Sample',
  role: 'clinician',
  preferred_language: 'en',
  is_active: true,
  created_at: '2026-10-01T10:00:00Z',
  updated_at: '2026-10-02T10:00:00Z',
  reports_count: 0,
};

const medicalProfile = {
  status: 'ok',
  profile: {
    id: 'mp-1',
    date_of_birth: '1980-05-17',
    gender: 'female',
    blood_group: 'O+',
    known_allergies: 'Penicillin, peanuts',
    chronic_conditions: 'Type 2 diabetes',
  },
};

const doctorProfile = (isVerified: boolean) => ({
  status: 'ok',
  profile: {
    id: 'dp-1',
    specialty: 'Cardiology',
    license_number: 'LIC-123',
    hospital: 'City Hospital',
    is_verified: isVerified,
  },
});

const caregiverProfile = (isVerified: boolean) => ({
  status: 'ok',
  profile: { id: 'cp-1', relationship: 'daughter', is_verified: isVerified },
});

const configure = ({ doctorVerified = false, caregiverVerified = false } = {}) => {
  mockedFetchApi.mockImplementation((url, options) => {
    const path = String(url);
    if ((options as { method?: string } | undefined)?.method === 'POST') return Promise.resolve({ status: 'ok', message: 'done' });
    if (path === '/api/v1/admin/users/user-1') return Promise.resolve({ status: 'ok', user });
    if (path.endsWith('/medical_profile')) return Promise.resolve(medicalProfile);
    if (path.endsWith('/doctor_profile')) return Promise.resolve(doctorProfile(doctorVerified));
    if (path.endsWith('/caregiver_profile')) return Promise.resolve(caregiverProfile(caregiverVerified));
    return Promise.resolve({ status: 'ok', items: [], sessions: [], logs: [], reminders: [] });
  });
};

const renderPage = () =>
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <UserDetailPage />
    </QueryClientProvider>
  );

const postCalls = () =>
  mockedFetchApi.mock.calls.filter(([, options]) => (options as { method?: string } | undefined)?.method === 'POST');

beforeEach(() => {
  mockedFetchApi.mockReset();
  mockCan = () => true;
  jest.spyOn(window, 'confirm').mockReturnValue(true);
});
afterEach(() => jest.restoreAllMocks());

describe('User detail profile cards', () => {
  it('shows the medical profile using the backend field names', async () => {
    configure();
    renderPage();
    expect(await screen.findByText('O+')).toBeInTheDocument();
    expect(screen.getByText('1980-05-17')).toBeInTheDocument();
    expect(screen.getByText('female')).toBeInTheDocument();
    expect(screen.getByText('Penicillin, peanuts')).toBeInTheDocument();
    // used to crash: chronic conditions arrive as text, not a list
    expect(screen.getByText('Type 2 diabetes')).toBeInTheDocument();
  });

  it('still accepts allergies and conditions sent as lists', async () => {
    mockedFetchApi.mockImplementation((url) => {
      const path = String(url);
      if (path === '/api/v1/admin/users/user-1') return Promise.resolve({ status: 'ok', user });
      if (path.endsWith('/medical_profile')) {
        return Promise.resolve({ status: 'ok', profile: { ...medicalProfile.profile, known_allergies: ['Dust', 'Latex'], chronic_conditions: ['Asthma'] } });
      }
      return Promise.resolve({ status: 'ok', profile: null, items: [] });
    });
    renderPage();
    expect(await screen.findByText('Dust, Latex')).toBeInTheDocument();
    expect(screen.getByText('Asthma')).toBeInTheDocument();
  });

  it('shows hospital and relationship', async () => {
    configure();
    renderPage();
    expect(await screen.findByText('City Hospital')).toBeInTheDocument();
    expect(screen.getByText('daughter')).toBeInTheDocument();
  });
});

describe('Verify clinician and caregiver', () => {
  it('verifies a clinician through the doctor_profile route', async () => {
    configure();
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Verify Credentials' }));
    await waitFor(() => expect(postCalls().length).toBeGreaterThan(0));
    expect(postCalls()[0][0]).toBe('/api/v1/admin/users/user-1/doctor_profile/verify');
  });

  it('verifies a caregiver through the caregiver_profile route', async () => {
    configure();
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Verify Caregiver' }));
    await waitFor(() => expect(postCalls().length).toBeGreaterThan(0));
    expect(postCalls()[0][0]).toBe('/api/v1/admin/users/user-1/caregiver_profile/verify');
  });

  it('hides the buttons once the profiles are verified', async () => {
    configure({ doctorVerified: true, caregiverVerified: true });
    renderPage();
    expect(await screen.findByText('Verified Clinician')).toBeInTheDocument();
    expect(screen.getByText('Verified Caregiver')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Verify Credentials' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Verify Caregiver' })).toBeNull();
  });

  it('hides the buttons from admins who cannot manage users', async () => {
    mockCan = (permission) => permission !== 'users.manage';
    configure();
    renderPage();
    await screen.findByText('City Hospital');
    expect(screen.queryByRole('button', { name: 'Verify Credentials' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Verify Caregiver' })).toBeNull();
  });
});
