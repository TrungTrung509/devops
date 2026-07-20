import http from 'k6/http';
import { sleep } from 'k6';

import { assertCourseRead, authHeaders, getConfig, login } from './common.js';

const { baseUrl, username, password } = getConfig();

export const options = {
  scenarios: {
    course_local_read: {
      executor: 'shared-iterations',
      vus: Number(__ENV.BENCH_VUS || 10),
      iterations: Number(__ENV.BENCH_ITERATIONS || 100),
      maxDuration: __ENV.BENCH_MAX_DURATION || '2m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<2000'],
  },
};

export function setup() {
  return {
    token: login(baseUrl, username, password),
    baseUrl,
  };
}

export default function (data) {
  const response = http.get(
    `${data.baseUrl}/courses?read_mode=local`,
    {
      headers: authHeaders(data.token),
      tags: {
        benchmark_case: 'course_local',
      },
    },
  );

  assertCourseRead(response, 'local');
  sleep(0.1);
}
