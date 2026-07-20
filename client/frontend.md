# Frontend Documentation - Hệ thống Đăng ký Tín chỉ

## 1. Tổng quan

### Công nghệ sử dụng

| Thư viện | Phiên bản | Mục đích |
|-----------|-----------|-----------|
| ReactJS | 18.3.1 | UI framework |
| Vite | 5.4.8 | Build tool & dev server |
| Ant Design | 5.21.2 | Component library |
| @tanstack/react-query | 5.56.2 | Server state management |
| React Router | 6.26.2 | Client-side routing |
| axios | 1.7.7 | HTTP client |
| sass | 1.79.3 | CSS preprocessor |

### Kiến trúc thư mục

```
client/
├── dist/                    # Build output (production)
├── node_modules/
├── src/
│   ├── app/
│   │   ├── layouts/        # MainLayout (sidebar + header + content)
│   │   ├── providers/      # AppProviders, AuthGuard
│   │   └── router/         # AppRouter
│   ├── components/         # Shared components (common, layout)
│   ├── features/           # Feature-based components (auth, registration, user)
│   ├── hooks/              # React Query hooks
│   ├── pages/              # Page components
│   ├── services/           # API layer (apiClient, auth, user, classSection, enrollment)
│   ├── styles/             # Global SCSS, variables, mixins
│   ├── utils/              # Utility functions
│   ├── constants/          # App constants
│   ├── assets/
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── package.json
└── vite.config.js
```

### Luồng dữ liệu

```
Component → Hook (useQuery/useMutation) → API Service → apiClient (axios)
                                                        ↓
                                                  Response interceptor
                                                        ↓
                                              { status, success, data }
```

---

## 2. Cách chạy dự án

### Yêu cầu

- Node.js 18+ (khuyến nghị Node.js 20 LTS)
- Backend FastAPI đang chạy tại `http://localhost:8000`

### Cài đặt

```bash
cd client
npm install
```

### Chạy dev server

```bash
npm run dev
# hoặc
node node_modules/vite/bin/vite.js
```

Dev server chạy tại `http://localhost:3000`. Proxy tự động chuyển request sang `http://localhost:8000`.

### Build production

```bash
npm run build
# Output: client/dist/
```

### Preview production build

```bash
npm run preview
```

---

## 3. Cấu hình môi trường

### Proxy (vite.config.js)

Backend API được proxy qua Vite dev server. Không cần file `.env`:

```javascript
proxy: {
  '/auth': { target: 'http://localhost:8000', changeOrigin: true },
  '/users': { target: 'http://localhost:8000', changeOrigin: true },
  '/branches': { target: 'http://localhost:8000', changeOrigin: true },
  '/semesters': { target: 'http://localhost:8000', changeOrigin: true },
  '/class-sections': { target: 'http://localhost:8000', changeOrigin: true },
  '/enrollments': { target: 'http://localhost:8000', changeOrigin: true },
  '/courses': { target: 'http://localhost:8000', changeOrigin: true },
  '/health': { target: 'http://localhost:8000', changeOrigin: true },
}
```

### Token storage

- Access token: `localStorage.getItem('access_token')`
- Refresh token: `localStorage.getItem('refresh_token')`

---

## 4. Mô tả từng module giao diện

### 4.1. Login Page (`/login`)

- **File**: `src/pages/LoginPage.jsx`
- **Styles**: `src/pages/LoginPage.module.scss`
- **Mô tả**: Trang đăng nhập với form Ant Design
- **API gọi**: `POST /auth/login`
- **Payload**: `{ username, password }` (form-urlencoded)
- **Response**: `{ access_token, refresh_token, token_type }`
- **Hành vi**:
  - Submit → gọi login API
  - Thành công → lưu token → redirect `/dashboard`
  - Thất bại → hiển thị Alert lỗi
  - Loading state khi đang submit
- **Demo account**: `admin` / `admin123`

### 4.2. Main Layout

- **File**: `src/app/layouts/MainLayout.jsx`
- **Styles**: `src/app/layouts/MainLayout.module.scss`
- **Mô tả**: Layout chính với sidebar trái, header trên, content ở giữa
- **Sidebar**:
  - Logo "ĐKTC PTIT"
  - Menu: Trang chủ, Đăng ký môn học
  - Nút collapse sidebar
  - Gradient background xanh đậm
- **Header**:
  - Avatar + tên người dùng + vai trò + mã SV
  - Dropdown menu: Thông tin cá nhân, Đăng xuất
  - Notification bell
- **Content**: Render outlet của React Router

### 4.3. Dashboard Page (`/dashboard`)

- **File**: `src/pages/DashboardPage.jsx`
- **Styles**: `src/pages/DashboardPage.module.scss`
- **Mô tả**: Trang chủ sau đăng nhập
- **API gọi**:
  - `GET /users/me` → thông tin sinh viên
  - `GET /enrollments/history` → lịch sử đăng ký
- **Thành phần**:
  - Welcome banner với gradient xanh
  - 3 Statistic cards (môn đã đăng ký, đang theo học, đã hoàn thành)
  - Thông tin sinh viên (họ tên, mã SV, giới tính, ngày sinh, SDT, cơ sở)
  - Bảng đăng ký gần đây (5 bản ghi gần nhất)
  - Nút "Đăng ký môn học" → link đến trang registration

### 4.4. Course Registration Page (`/registration`)

- **File**: `src/pages/CourseRegistrationPage.jsx`
- **Styles**: `src/pages/CourseRegistrationPage.module.scss`
- **Mô tả**: Trang trọng tâm - đăng ký học phần
- **API gọi**:
  - `GET /class-sections/` → danh sách lớp học phần mở
  - `GET /enrollments/history` → lịch sử đăng ký
  - `GET /branches/` → danh sách cơ sở (cho filter)
  - `POST /enrollments/register` → đăng ký
  - `DELETE /enrollments/cancel?maLopHP=xxx` → hủy đăng ký
- **Thành phần**:
  - Header với tiêu đề + nút làm mới
  - Filter bar: tìm kiếm theo từ khóa, lọc theo cơ sở
  - **Bảng trên**: Danh sách lớp học phần mở đăng ký
    - Columns: Mã LHP, Mã HP, Tên học phần, Nhóm, Cơ sở, Hình thức, Sĩ số, Trạng thái, Thao tác
    - Nút "Đăng ký" cho lớp chưa đăng ký, chưa full, chưa đóng
    - Tag "Đã đăng ký" cho lớp đã đăng ký
    - Tag "Full" / "Đã đóng" cho lớp không thể đăng ký
    - Filter frontend-side (tìm kiếm + lọc cơ sở)
  - **Bảng dưới**: Lớp đã đăng ký
    - Columns: Mã LHP, Tên học phần, Nhóm, Cơ sở, Ngày đăng ký, Trạng thái, Thao tác
    - Chỉ hiển thị các enrollment có `trangThaiDangKy === 'DaDangKy'`
    - Nút "Hủy" với Popconfirm xác nhận
  - **Modal đăng ký**: Xác nhận trước khi submit
    - Hiển thị thông tin lớp (mã, tên, cơ sở, hình thức, sĩ số)
    - Input ghi chú tùy chọn
    - Nút xác nhận → gọi register API
- **Invalidation**: Sau register/cancel → invalidate `enrollmentHistory` và `classSections`

### 4.5. Not Found Page (`/*`)

- **File**: `src/pages/NotFoundPage.jsx`
- **Mô tả**: Hiển thị khi route không tồn tại
- Nút quay về trang chủ

---

## 5. React Query

### Query Keys

| Key | Dùng cho |
|-----|----------|
| `['currentUser']` | `GET /users/me` |
| `['classSections', filters]` | `GET /class-sections/` |
| `['enrollmentHistory', maHocKy]` | `GET /enrollments/history` |
| `['branches']` | `GET /branches/` |
| `['semesters']` | `GET /semesters/` |

### Mutations

| Hook | API | Invalidate |
|------|-----|------------|
| `useLoginMutation` | `POST /auth/login` | — |
| `useLogoutMutation` | `POST /auth/logout` | clear all |
| `useRegisterEnrollmentMutation` | `POST /enrollments/register` | enrollmentHistory, classSections, currentUser |
| `useCancelEnrollmentMutation` | `DELETE /enrollments/cancel` | enrollmentHistory, classSections, currentUser |

### Cấu hình QueryClient

```javascript
staleTime: 5 phút
gcTime: 10 phút
retry: 1
refetchOnWindowFocus: false
```

---

## 6. API Layer

### apiClient.js

- Axios instance với base URL `/`
- Request interceptor: tự động gắn `Bearer {token}` từ localStorage
- Response interceptor: unwrap `{ status, success, data, message, errorr }`
- Error handling: 401 → clear token → redirect `/login`

### Auth Flow

```
1. User đăng nhập → POST /auth/login
2. Lưu access_token + refresh_token vào localStorage
3. Mọi request sau tự động có Authorization header
4. Backend trả 401 → interceptor clear token → redirect /login
5. Logout → xóa token → clear React Query cache → redirect /login
```

### Cached Data

| API | staleTime | Dùng chung |
|-----|-----------|-----------|
| `/users/me` | 5 phút | Dashboard, Header |
| `/class-sections/` | 2 phút | Registration |
| `/enrollments/history` | 2 phút | Registration, Dashboard |
| `/branches/` | 30 phút | Registration filter |
| `/semesters/` | 30 phút | — |

---

## 7. Backend Endpoints đang được sử dụng

### Endpoint đang dùng thật

| Method | Endpoint | Mục đích | Payload/Query |
|--------|----------|-----------|---------------|
| POST | `/auth/login` | Đăng nhập | `{username, password}` (form) |
| POST | `/auth/logout` | Đăng xuất | `{refresh_token}` |
| GET | `/users/me` | Lấy thông tin user | — |
| GET | `/branches/` | Lấy danh sách cơ sở | — |
| GET | `/semesters/` | Lấy danh sách học kỳ | — |
| GET | `/class-sections/` | Lấy danh sách lớp HP | `?keyword=&maCoSo=&maHocKy=` |
| GET | `/enrollments/history` | Lấy lịch sử đăng ký | `?maHocKy=` |
| POST | `/enrollments/register` | Đăng ký học phần | `{ma_lop_h_p, ghi_chu}` |
| DELETE | `/enrollments/cancel` | Hủy đăng ký | `?ma_lop_h_p=xxx` |

### Response format

Backend trả wrapper:

```json
{
  "status": 200,
  "success": true,
  "message": "Thành công",
  "data": { ... },
  "errorr": null
}
```

Frontend interceptor unwrap `data` và rethrow error nếu `success === false`.

---

## 8. Những phần chưa triển khai (backend chưa sẵn sàng)

### Chưa triển khai

1. **Eligibility check endpoint**: Backend chưa có endpoint riêng. Xử lý bằng confirmation modal + hiển thị lỗi từ register API.

2. **Personal schedule (`/schedules/my`)**: Backend chỉ có `GET /schedules/` (read-only). Chưa có endpoint schedule cá nhân. Chưa triển khai trang lịch học.

3. **Refresh token auto-retry**: Chưa implement auto-refresh. Nếu token hết hạn, redirect về login.

4. **Change password UI**: Backend có `PUT /users/change-password` nhưng chưa có UI.

5. **Student/Teacher profile edit**: Backend có schema nhưng chưa triển khai UI.

### Cách mở rộng sau này

**Thêm eligibility endpoint**: Khi backend bổ sung `GET /enrollments/eligibility?maLopHP=xxx`:
1. Tạo `eligibilityApi.js` với endpoint mới
2. Tạo `useEligibilityQuery` hook
3. Thay confirmation modal bằng eligibility check trước khi hiện modal đăng ký

**Thêm schedules/my endpoint**: Khi backend bổ sung `GET /schedules/my`:
1. Thêm route `/schedule` trong `AppRouter.jsx`
2. Tạo `SchedulePage.jsx` với calendar/table view
3. Thêm sidebar menu item cho "Thời khóa biểu"

---

## 9. SCSS Variables và Design System

### Màu sắc

```scss
$color-primary: #1677ff;      // Xanh chính
$color-success: #52c41a;     // Xanh lá
$color-warning: #faad14;     // Vàng
$color-error: #ff4d4f;       // Đỏ
$color-bg-layout: #f0f2f5;   // Nền layout
```

### Spacing

```scss
$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 12px;
$spacing-base: 16px;
$spacing-lg: 24px;
$spacing-xl: 32px;
```

### Border Radius

```scss
$radius-sm: 4px;
$radius-md: 8px;
$radius-lg: 12px;
$radius-xl: 16px;
```

### Breakpoints

```scss
$breakpoint-sm: 576px;   // mobile
$breakpoint-md: 768px;  // tablet
$breakpoint-lg: 992px;  // desktop
$breakpoint-xl: 1200px; // large desktop
```

---

## 10. Checklist test

### Trước khi demo

- [ ] Backend FastAPI đang chạy tại `http://localhost:8000`
- [ ] `npm install` đã chạy trong `client/`
- [ ] `npm run dev` chạy tại `http://localhost:3000`
- [ ] Login với `admin` / `admin123` thành công
- [ ] Dashboard hiển thị thông tin user
- [ ] Registration page load danh sách lớp
- [ ] Đăng ký 1 lớp thành công
- [ ] Hủy đăng ký thành công
- [ ] Responsive trên mobile (sidebar ẩn, content full width)

### Test cases

1. **Login thất bại**: Nhập sai password → hiển thị Alert lỗi
2. **Login thành công**: Redirect đến dashboard
3. **Unauthenticated access**: Truy cập `/dashboard` không token → redirect `/login`
4. **Token hết hạn**: Backend trả 401 → redirect `/login`
5. **Filter class sections**: Tìm kiếm theo tên → danh sách lọc đúng
6. **Filter theo cơ sở**: Chọn "Cơ sở Hà Nội" → chỉ hiển thị lớp HADONG
7. **Register lớp đã full**: Nút đăng ký disabled, hiển thị "Full"
8. **Register lớp đã đăng ký**: Hiển thị tag "Đã đăng ký"
9. **Cancel đăng ký**: Popconfirm → confirm → hủy thành công
10. **Logout**: Xóa token → redirect login

---

## 11. Known issues / Limitations

1. **SCSS @import deprecation**: Sass 3 sẽ không hỗ trợ `@import`. Hiện tại dùng được nhưng cần chuyển sang `@use` trong tương lai.

2. **Chunk size lớn**: Ant Design bundle ~1.2MB. Nên dùng dynamic import cho các page không dùng ngay.

3. **Không có refresh token auto-retry**: Token hết hạn sẽ redirect login. Cân nhắc implement Axios interceptor cho refresh.

4. **CORS**: Backend chưa có CORS middleware. Dev proxy hoạt động tốt. Production cần thêm CORS config ở backend.

5. **Không có ổ cứng offline**: Không lưu cache offline.

---

*Generated on 2026-04-25 | Backend source: `/app` | Frontend source: `/client`*
