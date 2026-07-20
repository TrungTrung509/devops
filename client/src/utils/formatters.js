/**
 * General utility functions
 */

/**
 * Format a date string to Vietnamese locale
 */
export function formatDate(dateStr, options = {}) {
  if (!dateStr) return '—';
  const defaultOptions = { day: '2-digit', month: '2-digit', year: 'numeric', ...options };
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', defaultOptions);
  } catch {
    return dateStr;
  }
}

/**
 * Format datetime
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Format semester display string
 */
export function formatSemester(semester) {
  if (!semester) return '—';
  return `HK${semester.kySo || ''} – ${semester.namHoc || ''}`;
}

/**
 * Map enrollment status to display properties
 */
export function getEnrollmentStatusProps(status) {
  const map = {
    DaDangKy: { color: 'processing', label: 'Đã đăng ký' },
    HoanThanh: { color: 'success', label: 'Hoàn thành' },
    DaHuy: { color: 'error', label: 'Đã hủy' },
  };
  return map[status] || { color: 'default', label: status || '—' };
}

/**
 * Map class section status to display properties
 */
export function getClassSectionStatusProps(status) {
  const map = {
    Mo: { color: 'success', label: 'Mở' },
    Dong: { color: 'warning', label: 'Đóng' },
    Huy: { color: 'error', label: 'Hủy' },
  };
  return map[status] || { color: 'default', label: status || '—' };
}

/**
 * Map study form to display string
 */
export function getStudyFormLabel(form) {
  const map = {
    Offline: 'Offline',
    Online: 'Online',
    Hybrid: 'Hybrid',
  };
  return map[form] || form || '—';
}

/**
 * Map course type to display string
 */
export function getCourseTypeLabel(type) {
  const map = {
    BatBuoc: 'Bắt buộc',
    TuChon: 'Tự chọn',
  };
  return map[type] || type || '—';
}

/**
 * Map gender to display string
 */
export function getGenderLabel(gender) {
  const map = {
    Nam: 'Nam',
    Nu: 'Nữ',
    Khac: 'Khác',
  };
  return map[gender] || gender || '—';
}

/**
 * Get branch display name
 */
export function getBranchLabel(maCoSo) {
  const map = {
    HADONG: 'Cơ sở Hà Nội',
    HOALAC: 'Cơ sở Hòa Lạc',
    NGOCTRUC: 'Cơ sở Ngọc Trục',
  };
  return map[maCoSo] || maCoSo || '—';
}

/**
 * Get display name from user object (Student or Teacher)
 */
export function getUserDisplayName(user) {
  if (!user) return '—';
  if (user.ho || user.ten) {
    return `${user.ho || ''} ${user.ten || ''}`.trim();
  }
  return user.username || user.email || '—';
}

/**
 * Get student ID or teacher ID from user object
 */
export function getUserCode(user) {
  if (!user) return '—';
  return user.maSV || user.maGV || user.userId || '—';
}

/**
 * Capitalize first letter
 */
export function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Build full name from Ho and Ten
 */
export function buildFullName(ho, ten) {
  return [ho, ten].filter(Boolean).join(' ');
}

/**
 * Map student status to display properties
 */
export function getStudentStatusProps(status) {
  const map = {
    DangHoc: { color: 'success', label: 'Đang học' },
    BaoLuu: { color: 'warning', label: 'Bảo lưu' },
    ThoiHoc: { color: 'error', label: 'Thôi học' },
    TotNghiep: { color: 'processing', label: 'Tốt nghiệp' },
  };
  return map[status] || { color: 'default', label: status || '—' };
}

/**
 * Map teacher status to display properties
 */
export function getTeacherStatusProps(status) {
  const map = {
    DangCongTac: { color: 'success', label: 'Đang công tác' },
    TamNghi: { color: 'warning', label: 'Tạm nghỉ' },
    NghiViec: { color: 'error', label: 'Nghỉ việc' },
  };
  return map[status] || { color: 'default', label: status || '—' };
}

/**
 * Map semester status to display properties
 */
export function getSemesterStatusProps(status) {
  const map = {
    SapMo: { color: 'default', label: 'Sắp mở' },
    DangDangKy: { color: 'processing', label: 'Đang đăng ký' },
    DangHoc: { color: 'success', label: 'Đang học' },
    DaKetThuc: { color: 'default', label: 'Đã kết thúc' },
  };
  return map[status] || { color: 'default', label: status || '—' };
}

/**
 * Map day of week number to label
 */
export function getDayOfWeekLabel(thu) {
  const map = {
    2: 'Thứ Hai',
    3: 'Thứ Ba',
    4: 'Thứ Tư',
    5: 'Thứ Năm',
    6: 'Thứ Sáu',
    7: 'Thứ Bảy',
    8: 'Chủ Nhật',
  };
  return map[thu] || `Thứ ${thu}` || '—';
}

/**
 * Map degree title
 */
export function getDegreeLabel(hocVi) {
  const map = {
    CN: 'Cử nhân',
    ThS: 'Thạc sĩ',
    TS: 'Tiến sĩ',
    PGS: 'Phó giáo sư',
    GS: 'Giáo sư',
  };
  return map[hocVi] || hocVi || '—';
}

/**
 * Map academic rank title
 */
export function getRankLabel(hocHam) {
  const map = {
    GiaoSu: 'Giáo sư',
    PhoGiaoSu: 'Phó giáo sư',
  };
  return map[hocHam] || hocHam || '—';
}

/**
 * Format time slot: tietBatDau + SoTiet -> "Tiết 1-3"
 */
export function formatTimeSlot(tietBatDau, soTiet) {
  if (!tietBatDau) return '—';
  const end = soTiet ? tietBatDau + soTiet - 1 : tietBatDau;
  return `Tiết ${tietBatDau}–${end}`;
}


// QUY UOC TIET HOC – 50 phut/tiet, nghi trua 12:00–13:00


/**
 * Thoi gian bat dau thuc cua tung tiet (gio:phut)
 */
const LESSON_TIME_START = {
  1: '07:00', 2: '08:00', 3: '09:00', 4: '10:00', 5: '11:00',
  6: '13:00', 7: '14:00', 8: '15:00', 9: '16:00', 10: '17:00',
};

/**
 * Thoi gian ket thuc thuc cua tung tiet (gio:phut)
 * Moi tiet 50 phut, gio ket thuc = gio bat dau + 50 phut
 */
const LESSON_TIME_END = {
  1: '07:50', 2: '08:50', 3: '09:50', 4: '10:50', 5: '11:50',
  6: '13:50', 7: '14:50', 8: '15:50', 9: '16:50', 10: '17:50',
};

/**
 * Mang tra ve gio bat dau + gio ket thuc cua tiet
 * @param {number} tietBatDau - Tiết bắt đầu (1-10)
 * @param {number} soTiet - Số tiết liên tiếp
 * @returns {{ start: string, end: string }}
 */
export function getLessonTimeRange(tietBatDau, soTiet) {
  if (!tietBatDau) return { start: '—', end: '—' };
  const start = LESSON_TIME_START[tietBatDau] || `${tietBatDau}:00`;
  // Tinh tiet ket thuc
  const endTiet = soTiet ? tietBatDau + soTiet - 1 : tietBatDau;
  // Neu tiet ket thuc > 5 -> chuyen sang buoi chieu
  const end = endTiet <= 5
    ? LESSON_TIME_END[endTiet] || `${endTiet + 1}:00`
    : LESSON_TIME_END[endTiet] || `${endTiet}:00`;
  return { start, end };
}

/**
 * Tra ve chuoi thoi gian "HH:MM – HH:MM"
 * @param {number} tietBatDau
 * @param {number} soTiet
 * @returns {string}
 */
export function formatLessonTime(tietBatDau, soTiet) {
  const { start, end } = getLessonTimeRange(tietBatDau, soTiet);
  return `${start} – ${end}`;
}

/**
 * Map thu trong tuan (2-8) -> label "Thu Hai", "Thu Ba"...
 */
export function getWeekdayLabel(thu) {
  const map = {
    2: 'Thứ Hai',
    3: 'Thứ Ba',
    4: 'Thứ Tư',
    5: 'Thứ Năm',
    6: 'Thứ Sáu',
    7: 'Thứ Bảy',
    8: 'Chủ Nhật',
  };
  return map[thu] || `T${thu}`;
}

/**
 * Tra ve css color cho tung tiet hoc
 * Buoi sang (tiet 1-5): xanh duong nhat
 * Buoi chieu (tiet 6-10): cam
 */
export function getLessonSlotColor(tietBatDau) {
  if (tietBatDau >= 1 && tietBatDau <= 5) return '#1677ff';
  return '#fa8c16';
}

/**
 * Tra ve badge status color cho thu trong tuan
 * T2-T5: xanh duong, T6-T7: cam, CN: do
 */
export function getWeekdayColor(thu) {
  const map = {
    2: 'blue',
    3: 'cyan',
    4: 'geekblue',
    5: 'purple',
    6: 'orange',
    7: 'gold',
    8: 'red',
  };
  return map[thu] || 'default';
}

/**
 * Build noi dung Popover cho 1 buoi hoc
 * Tra ve component-ready data
 */
export function buildSchedulePopoverItem(item) {
  const thuLabel = getWeekdayLabel(item.ThuTrongTuan);
  const weekdayColor = getWeekdayColor(item.ThuTrongTuan);
  const timeRange = formatLessonTime(item.TietBatDau, item.SoTiet);
  const tietLabel = item.SoTiet > 1
    ? `${item.TietBatDau}–${item.TietBatDau + item.SoTiet - 1}`
    : `${item.TietBatDau}`;
  const phong = item.TenPhong || item.MaPhong || '—';
  const ghiChu = item.GhiChu;

  return { thuLabel, weekdayColor, timeRange, tietLabel, phong, ghiChu };
}

/**
 * Format a date value to dd/MM/yyyy
 * @param {string|Date} value - ISO date string or Date
 * @returns {string} formatted date or fallback
 */
export function formatScheduleDate(value) {
  if (!value) return 'Chưa cập nhật';
  try {
    const d = new Date(value);
    if (isNaN(d.getTime())) return 'Chưa cập nhật';
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  } catch {
    return 'Chưa cập nhật';
  }
}

/**
 * Format a date range from two values.
 * @param {string|Date} start
 * @param {string|Date} end
 * @returns {string} e.g. "15/08/2025 - 30/09/2025"
 */
export function formatDateRange(start, end) {
  const s = formatScheduleDate(start);
  const e = formatScheduleDate(end);
  if (s === 'Chưa cập nhật' && e === 'Chưa cập nhật') return 'Chưa cập nhật';
  if (s === 'Chưa cập nhật') return `Từ ${e}`;
  if (e === 'Chưa cập nhật') return `Từ ${s}`;
  return `${s} – ${e}`;
}

/**
 * Determine the period label for a schedule entry.
 * Priority: GhiChu if present and meaningful, else "Giai đoạn {index+1}".
 * @param {object} schedule - LichHoc entry
 * @param {number} index - position in LichHoc array (0-based)
 * @returns {string} period label
 */
export function formatPeriodLabel(schedule, index) {
  const ghiChu = schedule.GhiChu;
  if (ghiChu && ghiChu.trim()) {
    const lower = ghiChu.toLowerCase();
    // Match "nua ky dau", "nua ky sau", "ky dau", "ky sau", "dau ky", "sau ky"
    if (lower.includes('dau') && !lower.includes('sau')) {
      return 'Nửa kỳ đầu';
    }
    if (lower.includes('sau')) {
      return 'Nửa kỳ sau';
    }
    // Return the GhiChu as-is if it doesn't match known patterns
    return ghiChu.trim();
  }
  return `Giai đoạn ${index + 1}`;
}

/**
 * Get a CSS color for period badge (alternate between two shades).
 * @param {number} index - schedule position in LichHoc array
 * @returns {string} CSS color
 */
export function getPeriodBadgeColor(index) {
  // Alternate between green-ish and blue-ish to distinguish periods
  return index === 0 ? '#52c41a' : '#1677ff';
}

/**
 * Format lesson range string: "Tiết 1-3"
 * @param {number} tietBatDau
 * @param {number} soTiet
 * @returns {string}
 */
export function formatLessonRange(tietBatDau, soTiet) {
  if (!tietBatDau) return '—';
  const end = soTiet ? tietBatDau + soTiet - 1 : tietBatDau;
  return `Tiết ${tietBatDau}–${end}`;
}
