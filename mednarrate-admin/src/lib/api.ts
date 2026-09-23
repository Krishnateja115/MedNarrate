const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  public status: number;
  public data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

function generateRequestId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'req-' + Math.random().toString(36).substring(2, 15);
}

interface FetchOptions extends RequestInit {
  data?: any;
  params?: Record<string, string>;
}

export async function fetchApi<T = any>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { data, params, headers, ...customConfig } = options;

  let url = `${API_BASE_URL}${endpoint}`;
  
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }

  const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null;

  const config: RequestInit = {
    method: data ? 'POST' : 'GET',
    ...customConfig,
    headers: {
      'Content-Type': data ? 'application/json' : '',
      'Accept': 'application/json',
      'X-Request-ID': generateRequestId(),
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...headers,
    },
  };

  // Clean empty Content-Type if we're not sending data
  if (!data && (config.headers as Record<string, string>)['Content-Type'] === '') {
    delete (config.headers as Record<string, string>)['Content-Type'];
  }

  if (data) {
    config.body = JSON.stringify(data);
  }

  let response: Response;
  try {
    response = await fetch(url, config);
  } catch (error) {
    // Network error
    throw new ApiError(0, 'Network error. Please check your connection.');
  }

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }

    const message = errorData.detail || errorData.message || 'An error occurred';
    
    // Log safely without bodies
    console.error(`[API Error] ${response.status} ${config.method} ${url}`);

    if (response.status === 401 && typeof window !== 'undefined') {
      // Handle unauthorized (we can dispatch a custom event to force logout, or let AuthContext handle it)
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    }

    throw new ApiError(response.status, message, errorData);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
