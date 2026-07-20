import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    scenarios: {
        deadlock_demo: {
            executor: 'per-vu-iterations',
            vus: 2, 
            iterations: 30,
            maxDuration: '5m',
        },
    },
};

const BASE_URL = __ENV.BENCH_BASE_URL || 'http://backend:8000';
const CLASS_A = __ENV.CLASS_A || 'HADONG_GDTC1102_01';
const CLASS_B = __ENV.CLASS_B || 'HADONG_GDTC1102_02';

export function setup() {
    let tokens = [];
    const users = [
        { username: __ENV.USER1 || 'SVHD26CNTT001', password: __ENV.PASS1 || '123456' },
        { username: __ENV.USER2 || 'SVHD26CNTT002', password: __ENV.PASS2 || '123456' }
    ];

    for (let i = 0; i < users.length; i++) {
        let u = users[i];
        const res = http.post(`${BASE_URL}/auth/login`, {
            username: u.username,
            password: u.password,
            grant_type: 'password'
        }, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
        
        if (res.status !== 200) {
            console.log(`[!] Login failed for ${u.username}: ${res.status} - ${res.body}`);
        }
        
        tokens.push({
            username: u.username,
            token: res.json('access_token')
        });
    }
    return { students: tokens };
}

export default function (data) {
    const myData = data.students[__VU - 1];
    const token = myData.token;
    const userName = myData.username;
    
    let targetClass;
    // VU lẻ đi hướng A, VU chẵn đi hướng B ở bước đầu
    const isGroupA = (__VU % 2 === 1);
    
    if (__ITER === 0) {
        targetClass = isGroupA ? CLASS_A : CLASS_B;
    } else {
        const isToggle = (__ITER % 2 === 1);
        if (isGroupA) {
            targetClass = isToggle ? CLASS_B : CLASS_A;
        } else {
            targetClass = isToggle ? CLASS_A : CLASS_B;
        }
    }

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };

    const payload = JSON.stringify({
        MaLopHP: targetClass,
        GhiChu: `Stress Test - VU ${__VU} - Iter ${__ITER}`
    });

    const res = http.post(`${BASE_URL}/enrollments/register`, payload, { headers });

    if (res.status === 409) {
        console.log(`[🔥 DEADLOCK] ${userName} bị kẹt chéo! Chờ hệ thống Retry...`);
    } else if (res.status !== 200 && res.status !== 201) {
        console.log(`[!] ${userName} lỗi ${res.status}: ${res.body}`);
    }

    check(res, {
        'Success or Deadlock Retry': (r) => [200, 201, 409].includes(r.status),
    });

    sleep(0.01);
}
