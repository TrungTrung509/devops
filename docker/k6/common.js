import http from 'k6/http';
import { check, fail } from 'k6';

export function getConfig() {
  const username = __ENV.BENCH_USERNAME || '';
  const password = __ENV.BENCH_PASSWORD || '';
  const baseUrl = (__ENV.BENCH_BASE_URL || 'http://backend:8000').replace(/\/+$/, '');
  const targetSite = (__ENV.BENCH_TARGET_SITE || 'HADONG').toUpperCase();

  if (!username || !password) {
    fail('Can set BENCH_USERNAME and BENCH_PASSWORD before running k6.');
  }

  return { baseUrl, username, password, targetSite };
}

export function login(baseUrl, username, password) {
  const response = http.post(
    `${baseUrl}/auth/login`,
    {
      username,
      password,
      grant_type: 'password',
    },
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      tags: {
        phase: 'login',
      },
    },
  );

  const ok = check(response, {
    'login status is 200': (res) => res.status === 200,
    'login returns access token': (res) => {
      const body = safeJson(res);
      return Boolean(body && body.access_token);
    },
  });

  if (!ok) {
    fail(`Login failed with status ${response.status}: ${response.body}`);
  }

  return safeJson(response).access_token;
}

export function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

export function safeJson(response) {
  try {
    return response.json();
  } catch (_error) {
    return null;
  }
}

export function assertCourseRead(response, expectedMode) {
  return check(response, {
    'course read status is 200': (res) => res.status === 200,
    'course read returns success': (res) => {
      const body = safeJson(res);
      return Boolean(body && body.success === true);
    },
    'course read mode matches expectation': (res) => {
      const body = safeJson(res);
      return body?.data?.read_context?.read_mode === expectedMode;
    },
  });
}
