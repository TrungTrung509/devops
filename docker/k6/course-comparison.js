import http from 'k6/http';
import { fail, sleep } from 'k6';
import exec from 'k6/execution';

import { assertCourseRead, authHeaders, getConfig, login } from './common.js';

const { baseUrl, username, password, targetSite } = getConfig();
const localIterations = Number(__ENV.BENCH_ITERATIONS || 100);
const remoteIterations = Number(__ENV.BENCH_REMOTE_ITERATIONS || localIterations);
const totalIterations = localIterations + remoteIterations;

export const options = {
  scenarios: {
    course_read_comparison: {
      executor: 'shared-iterations',
      vus: Number(__ENV.BENCH_VUS || 10),
      iterations: totalIterations,
      maxDuration: __ENV.BENCH_MAX_DURATION || '5m',
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
    localIterations,
    totalIterations,
  };
}

export default function (data) {
  const iteration = exec.scenario.iterationInTest;
  const isLocalRun = iteration < data.localIterations;
  const readMode = isLocalRun ? 'local' : 'remote';
  const url = isLocalRun
    ? `${data.baseUrl}/courses?read_mode=local`
    : `${data.baseUrl}/courses?read_mode=remote&target_site=${data.targetSite}`;

  const response = http.get(url, {
    headers: authHeaders(data.token),
    tags: {
      benchmark_case: isLocalRun ? 'course_local' : 'course_remote',
      target_site: isLocalRun ? 'LOCAL' : data.targetSite,
    },
  });

  const ok = assertCourseRead(response, readMode);
  if (!ok) {
    fail(`Course ${readMode} read failed at iteration ${iteration}`);
  }

  sleep(0.1);
}
