/**
 * App-wide constants
 */

export const APP_NAME = 'Hệ thống Đăng ký Tín chỉ';
export const APP_SHORT_NAME = 'ĐKTC';

// Enrollment status
export const ENROLLMENT_STATUS = {
  DANG_KY: 'DaDangKy',
  HOAN_THANH: 'HoanThanh',
  DA_HUY: 'DaHuy',
};

// Class section status
export const CLASS_SECTION_STATUS = {
  MO: 'Mo',
  DONG: 'Dong',
  HUY: 'Huy',
};

// User roles
export const USER_ROLE = {
  SINH_VIEN: 'SinhVien',
  GIANG_VIEN: 'GiangVien',
  ADMIN: 'Admin',
};

// Study forms
export const STUDY_FORM = {
  OFFLINE: 'Offline',
  ONLINE: 'Online',
  HYBRID: 'Hybrid',
};

// Navigation items for sidebar
export const SIDEBAR_MENU = [
  {
    key: 'dashboard',
    label: 'Trang chủ',
    path: '/dashboard',
    icon: 'HomeOutlined',
  },
  {
    key: 'registration',
    label: 'Đăng ký môn học',
    path: '/registration',
    icon: 'BookOutlined',
  },
];

// Default pagination
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = ['10', '20', '50', '100'];

// Day of week labels (Monday = 2 in backend)
export const DAY_LABELS = {
  2: 'Thứ Hai',
  3: 'Thứ Ba',
  4: 'Thứ Tư',
  5: 'Thứ Năm',
  6: 'Thứ Sáu',
  7: 'Thứ Bảy',
  8: 'Chủ Nhật',
};

// Semester status labels
export const SEMESTER_STATUS_LABELS = {
  SapMo: 'Sắp mở',
  DangDangKy: 'Đang đăng ký',
  DangHoc: 'Đang học',
  DaKetThuc: 'Đã kết thúc',
};
