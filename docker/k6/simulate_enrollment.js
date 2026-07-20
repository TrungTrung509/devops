import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    // Scenario 1: Students registering and canceling courses sequentially
    student_registration: {
      executor: 'constant-vus',
      vus: 60, // 60 students active at the same time
      duration: '1m',
      exec: 'registrationFlow',
    },
    // Scenario 2: Users browsing courses and checking timetables
    system_viewers: {
      executor: 'constant-vus',
      vus: 40, // 40 viewers active at the same time
      duration: '1m',
      exec: 'viewerFlow',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'], // Allow minor failures under stress
    http_req_duration: ['p(95)<3000'], // 95% of requests should be under 3s
  },
};

const BASE_URL = __ENV.BENCH_BASE_URL || 'http://host.docker.internal:8000';
const SITES = ['HADONG', 'HOALAC', 'NGOCTRUC'];
const SITE_CODES = {
  'HADONG': 'HD',
  'HOALAC': 'HL',
  'NGOCTRUC': 'NT',
};
const COURSES = [
  'GDTC1102',
  'MLN1102',
  'ENG1101',
  'BAS1204',
  'BAS1224',
  'BAS1105',
  'INT1319',
  'INT1155'
];

export function setup() {
  // Pre-login users to obtain JWT tokens.
  // We log in 60 students (20 per site) and 40 viewers.
  const students = [];
  const viewers = [];

  // Log in 60 students
  for (let i = 1; i <= 60; i++) {
    const site = SITES[(i - 1) % SITES.length];
    const code = SITE_CODES[site];
    const username = `SV${code}26CNTT${String(i).padStart(3, '0')}`;
    const res = http.post(`${BASE_URL}/auth/login`, {
      username: username,
      password: '123456',
      grant_type: 'password'
    }, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });

    if (res.status === 200) {
      students.push({
        username: username,
        site: site,
        token: res.json('access_token')
      });
    } else {
      console.log(`Failed to login student ${username}: ${res.status} ${res.body}`);
    }
  }

  // Log in 40 viewers (can be teachers or students)
  for (let i = 61; i <= 100; i++) {
    const site = SITES[(i - 1) % SITES.length];
    const code = SITE_CODES[site];
    const username = `SV${code}26CNTT${String(i).padStart(3, '0')}`;
    const res = http.post(`${BASE_URL}/auth/login`, {
      username: username,
      password: '123456',
      grant_type: 'password'
    }, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });

    if (res.status === 200) {
      viewers.push({
        username: username,
        site: site,
        token: res.json('access_token')
      });
    }
  }

  console.log(`Setup complete: logged in ${students.length} students and ${viewers.length} viewers.`);
  return { students, viewers };
}

// Scenario 1: Registration Flow
export function registrationFlow(data) {
  const student = data.students[__VU - 1];
  if (!student) return;

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${student.token}`
  };

  const registeredClasses = [];

  // 1. Register for all 8 courses sequentially
  for (const course of COURSES) {
    // Choose a random section from 01 to 15
    const sectionNum = String(Math.floor(Math.random() * 15) + 1).padStart(2, '0');
    const classCode = `${student.site}_${course}_${sectionNum}`;

    const payload = JSON.stringify({ MaLopHP: classCode });
    const res = http.post(`${BASE_URL}/enrollments/register`, payload, { headers });

    const success = (res.status === 200 || res.status === 201);
    if (success) {
      registeredClasses.push(classCode);
    }

    check(res, {
      'Register status 201 or 400/409': (r) => [200, 201, 400, 409].includes(r.status),
    });

    sleep(0.1); // Small delay between registrations
  }

  console.log(`Student ${student.username} attempted all courses. Registered in ${registeredClasses.length}/8 classes.`);

  // 2. Hold the seats for 2 seconds to simulate reviewing the schedule
  sleep(2.0);

  // 3. Cancel all successfully registered classes to clean up database for the next iteration
  for (const classCode of registeredClasses) {
    const res = http.del(`${BASE_URL}/enrollments/cancel?maLopHP=${classCode}`, null, { headers });
    check(res, {
      'Cancel status is 200': (r) => r.status === 200,
    });
    sleep(0.05);
  }

  sleep(1.0); // Wait before next iteration
}

// Scenario 2: Viewer Flow
export function viewerFlow(data) {
  const viewer = data.viewers[__VU - 1];
  if (!viewer) return;

  const headers = {
    'Authorization': `Bearer ${viewer.token}`
  };

  // View course list
  const resCourses = http.get(`${BASE_URL}/courses`, { headers });
  check(resCourses, {
    'Get courses status 200': (r) => r.status === 200,
  });

  sleep(0.5);

  // View timetable
  const resTimetable = http.get(`${BASE_URL}/enrollments/timetable`, { headers });
  check(resTimetable, {
    'Get timetable status 200': (r) => r.status === 200,
  });

  sleep(0.5);

  // View history
  const resHistory = http.get(`${BASE_URL}/enrollments/history`, { headers });
  check(resHistory, {
    'Get history status 200': (r) => r.status === 200,
  });

  sleep(1.0);
}
