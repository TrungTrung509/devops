import http from 'k6/http';
import { sleep } from 'k6';

import { assertCourseRead, authHeaders, getConfig, login } from './common.js';

const { baseUrl, username, password, targetSite } = getConfig();

export const options = {
  scenarios: {
    course_remote_read: {
      executor: 'shared-iterations',
      vus: Number(__ENV.BENCH_VUS || 10),
      iterations: Number(__ENV.BENCH_REMOTE_ITERATIONS || __ENV.BENCH_ITERATIONS || 100),
      maxDuration: __ENV.BENCH_MAX_DURATION || '2m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<3000'],
  },
};

export function setup() {
  return {
    token: login(baseUrl, username, password),
    baseUrl,
    targetSite,
  };
}

export default function (data) {
  const response = http.get(
    `${data.baseUrl}/courses?read_mode=remote&target_site=${data.targetSite}`,
    {
      headers: authHeaders(data.token),
      tags: {
        benchmark_case: 'course_remote',
        target_site: data.targetSite,
      },
    },
  );

  assertCourseRead(response, 'remote');
  sleep(0.1);
}
