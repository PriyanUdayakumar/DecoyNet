export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  constructor({ status, code, message, details }) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class NetworkError extends Error {
  constructor(message = 'Unable to connect to the DecoyNet backend.') {
    super(message);
    this.name = 'NetworkError';
    this.code = 'network_error';
  }
}

function buildUrl(path, params) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  });
  return url;
}

export async function request(path, { method = 'GET', body, params, signal } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (globalThis.crypto?.randomUUID) {
    headers['X-Correlation-ID'] = globalThis.crypto.randomUUID();
  }

  let response;
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new NetworkError();
  }

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new ApiError({
      status: response.status,
      code: data?.error || 'request_failed',
      message: data?.message || data?.detail?.[0]?.msg || `Request failed with ${response.status}`,
      details: data,
    });
  }
  return data;
}
