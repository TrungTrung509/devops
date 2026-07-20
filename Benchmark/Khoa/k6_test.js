import http from "k6/http";
import { check, sleep } from "k6";
import { randomIntBetween } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";

export const options = {
  stages: [
    { duration: "30s", target: 500 },
    { duration: "1m30s", target: 1000 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<3000"],
    "http_req_failed{scenario:default}": ["rate<0.5"],
  },
};

const SITES = ["CNTT", "CB", "NN", "KT", "DT"];
const BASE_URL = "http://bench_backend_khoa:8000";
const HEADERS = { "Content-Type": "application/json" };
const COURSES = ["IT01", "IT02", "IT03"];

// Khoa: 3 môn × 60 lớp/site, index 1-60, 61-120, 121-180
const COURSE_RANGES = {
  IT01: [1, 60],
  IT02: [61, 120],
  IT03: [121, 180],
};

function pickClass(site, maHP) {
  const [min, max] = COURSE_RANGES[maHP];
  const idx = randomIntBetween(min, max);
  return `${site}_${maHP}_${idx.toString().padStart(3, "0")}`;
}

function post(path, body) {
  return http.post(`${BASE_URL}${path}`, JSON.stringify(body), {
    headers: HEADERS,
  });
}
function del(path, body) {
  return http.request("DELETE", `${BASE_URL}${path}`, JSON.stringify(body), {
    headers: HEADERS,
  });
}

// VU-local state to track successful enrollments: { [maHP]: maLopHP }
const myEnrollments = {};

export default function () {
  const siteIdx = __VU % SITES.length;
  const homeSite = SITES[siteIdx];
  const studentNum = ((__VU - 1) % 2400) + 1; // 2.400 SV/site
  const userId = `SV${homeSite}${studentNum.toString().padStart(4, "0")}`;

  const rand = Math.random();

  // Helper functions to get unregistered/registered courses
  const getUnregisteredCourses = () => COURSES.filter((c) => !myEnrollments[c]);
  const getRegisteredCourses = () => Object.keys(myEnrollments);

  if (rand < 0.6) {
    // ĐĂNG KÝ 1 MÔN (hoặc đổi lớp nếu đã đăng ký hết)

    const unregistered = getUnregisteredCourses();
    if (unregistered.length > 0) {
      const maHP =
        unregistered[Math.floor(Math.random() * unregistered.length)];
      const targetSite =
        Math.random() < 0.55
          ? homeSite
          : SITES.filter((s) => s !== homeSite)[randomIntBetween(0, 3)];
      const maLopHP = pickClass(targetSite, maHP);

      const res = post("/enrollments/register-bench", {
        userId,
        MaLopHP: maLopHP,
      });
      const success = res.status === 201;
      if (success) {
        myEnrollments[maHP] = maLopHP;
      }
      check(res, {
        "[REG] Success (201)": (r) => r.status === 201,
        "[REG] Schedule Conflict (409)": (r) => r.status === 409,
        "[REG] Class Full (400)": (r) => r.status === 400,
        "[REG] Timeout/Deadlock (503)": (r) => r.status === 503,
      });
    } else {
      // Đã đăng ký hết 3 môn -> Thực hiện ĐỔI LỚP (SWAP)
      const registered = getRegisteredCourses();
      const maHP = registered[Math.floor(Math.random() * registered.length)];
      const oldMaLopHP = myEnrollments[maHP];
      const targetSite =
        Math.random() < 0.55
          ? homeSite
          : SITES.filter((s) => s !== homeSite)[randomIntBetween(0, 3)];
      let newMaLopHP = pickClass(targetSite, maHP);
      while (newMaLopHP === oldMaLopHP) {
        newMaLopHP = pickClass(targetSite, maHP);
      }

      const res = post("/enrollments/register-bench", {
        userId,
        MaLopHP: newMaLopHP,
      });
      const success = res.status === 201;
      if (success) {
        myEnrollments[maHP] = newMaLopHP;
      }
      check(res, {
        "[SWAP] Success (201)": (r) => r.status === 201,
        "[SWAP] Timeout/Deadlock (503)": (r) => r.status === 503,
        "[SWAP] Error (4xx)": (r) => r.status >= 400 && r.status < 500,
      });
    }
  } else if (rand < 0.8) {
    // ĐĂNG KÝ NHANH CẢ 3 MÔN (stress scenario)

    for (const maHP of COURSES) {
      const targetSite =
        Math.random() < 0.55
          ? homeSite
          : SITES.filter((s) => s !== homeSite)[randomIntBetween(0, 3)];

      const oldMaLopHP = myEnrollments[maHP];
      let maLopHP = pickClass(targetSite, maHP);
      if (oldMaLopHP) {
        while (maLopHP === oldMaLopHP) {
          maLopHP = pickClass(targetSite, maHP);
        }
      }

      const res = post("/enrollments/register-bench", {
        userId,
        MaLopHP: maLopHP,
      });
      const success = res.status === 201;
      if (success) {
        myEnrollments[maHP] = maLopHP;
      }
      check(res, {
        "[FULL-REG] OK (not 5xx)": (r) => r.status < 500 || r.status === 503,
      });
    }
  } else if (rand < 0.9) {
    // ĐỔI LỚP (gọi register với lớp khác cùng môn)

    const registered = getRegisteredCourses();
    if (registered.length > 0) {
      const maHP = registered[Math.floor(Math.random() * registered.length)];
      const oldMaLopHP = myEnrollments[maHP];
      const targetSite =
        Math.random() < 0.55
          ? homeSite
          : SITES.filter((s) => s !== homeSite)[randomIntBetween(0, 3)];
      let newMaLopHP = pickClass(targetSite, maHP);
      while (newMaLopHP === oldMaLopHP) {
        newMaLopHP = pickClass(targetSite, maHP);
      }

      const res = post("/enrollments/register-bench", {
        userId,
        MaLopHP: newMaLopHP,
      });
      const success = res.status === 201;
      if (success) {
        myEnrollments[maHP] = newMaLopHP;
      }
      check(res, {
        "[SWAP] Success (201)": (r) => r.status === 201,
        "[SWAP] Timeout/Deadlock (503)": (r) => r.status === 503,
        "[SWAP] Error (4xx)": (r) => r.status >= 400 && r.status < 500,
      });
    } else {
      // Chưa đăng ký môn nào -> Đăng ký mới 1 môn
      const unregistered = getUnregisteredCourses();
      if (unregistered.length > 0) {
        const maHP =
          unregistered[Math.floor(Math.random() * unregistered.length)];
        const targetSite =
          Math.random() < 0.55
            ? homeSite
            : SITES.filter((s) => s !== homeSite)[randomIntBetween(0, 3)];
        const maLopHP = pickClass(targetSite, maHP);

        const res = post("/enrollments/register-bench", {
          userId,
          MaLopHP: maLopHP,
        });
        const success = res.status === 201;
        if (success) {
          myEnrollments[maHP] = maLopHP;
        }
        check(res, {
          "[REG] Success (201)": (r) => r.status === 201,
        });
      }
    }
  } else {
    // HỦY ĐĂNG KÝ (Hủy thực sự lớp đang đăng ký)

    const registered = getRegisteredCourses();
    if (registered.length > 0) {
      const maHP = registered[Math.floor(Math.random() * registered.length)];
      const maLopHP = myEnrollments[maHP];

      const res = del("/enrollments/cancel-bench", {
        userId,
        MaLopHP: maLopHP,
      });
      const success = res.status === 200;
      if (success) {
        delete myEnrollments[maHP];
      }
      check(res, {
        "[CANCEL] Success (200)": (r) => r.status === 200,
        "[CANCEL] Not Found (404)": (r) => r.status === 404,
      });
    } else {
      // Không có môn nào để hủy -> Đăng ký mới 1 môn
      const unregistered = getUnregisteredCourses();
      if (unregistered.length > 0) {
        const maHP =
          unregistered[Math.floor(Math.random() * unregistered.length)];
        const targetSite =
          Math.random() < 0.55
            ? homeSite
            : SITES.filter((s) => s !== homeSite)[randomIntBetween(0, 3)];
        const maLopHP = pickClass(targetSite, maHP);

        const res = post("/enrollments/register-bench", {
          userId,
          MaLopHP: maLopHP,
        });
        const success = res.status === 201;
        if (success) {
          myEnrollments[maHP] = maLopHP;
        }
        check(res, {
          "[REG] Success (201)": (r) => r.status === 201,
        });
      }
    }
  }

  sleep(0.8);
}
