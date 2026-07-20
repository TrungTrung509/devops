import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom';
import AuthGuard from '@/app/providers/AuthGuard';
import AdminGuard from '@/app/providers/AdminGuard';
import StudentGuard from '@/app/providers/StudentGuard';
import TeacherGuard from '@/app/providers/TeacherGuard';
import AdminLayout from '@/app/admin/layouts/AdminLayout';
import StudentLayout from '@/app/student/layouts/StudentLayout';
import TeacherLayout from '@/app/teacher/layouts/TeacherLayout';
import LoginPage from '@/pages/LoginPage';
import NotFoundPage from '@/pages/NotFoundPage';
import AdminDashboardPage from '@/app/admin/pages/AdminDashboardPage';
import AdminBranchesPage from '@/app/admin/pages/AdminBranchesPage';
import AdminDepartmentsPage from '@/app/admin/pages/AdminDepartmentsPage';
import AdminTeachersPage from '@/app/admin/pages/AdminTeachersPage';
import AdminStudentsPage from '@/app/admin/pages/AdminStudentsPage';
import AdminCoursesPage from '@/app/admin/pages/AdminCoursesPage';
import AdminSemestersPage from '@/app/admin/pages/AdminSemestersPage';
import AdminClassroomsPage from '@/app/admin/pages/AdminClassroomsPage';
import AdminClassSectionsPage from '@/app/admin/pages/AdminClassSectionsPage';
import AdminFailoverPage from '@/app/admin/pages/AdminFailoverPage';
import StudentDashboardPage from '@/app/student/pages/StudentDashboardPage';
import StudentProfilePage from '@/app/student/pages/StudentProfilePage';
import StudentClassSectionsPage from '@/app/student/pages/StudentClassSectionsPage';
import StudentEnrollmentsPage from '@/app/student/pages/StudentEnrollmentsPage';
import StudentSchedulePage from '@/app/student/pages/StudentSchedulePage';
import TeacherDashboardPage from '@/app/teacher/pages/TeacherDashboardPage';
import TeacherProfilePage from '@/app/teacher/pages/TeacherProfilePage';
import TeacherClassSectionsPage from '@/app/teacher/pages/TeacherClassSectionsPage';
import TeacherSchedulePage from '@/app/teacher/pages/TeacherSchedulePage';

const router = createBrowserRouter([
  // Public
  { path: 'login', element: <LoginPage /> },

  // All authenticated routes (AuthGuard checks login)
  {
    element: <AuthGuard />,
    children: [
      // ============ Admin Portal ============
      {
        element: (
          <AdminGuard>
            <AdminLayout />
          </AdminGuard>
        ),
        children: [
          { path: 'admin', element: <Navigate to="/admin/dashboard" replace /> },
          { path: 'admin/dashboard', element: <AdminDashboardPage /> },
          { path: 'admin/branches', element: <AdminBranchesPage /> },
          { path: 'admin/departments', element: <AdminDepartmentsPage /> },
          { path: 'admin/teachers', element: <AdminTeachersPage /> },
          { path: 'admin/students', element: <AdminStudentsPage /> },
          { path: 'admin/courses', element: <AdminCoursesPage /> },
          { path: 'admin/semesters', element: <AdminSemestersPage /> },
          { path: 'admin/classrooms', element: <AdminClassroomsPage /> },
          { path: 'admin/class-sections', element: <AdminClassSectionsPage /> },
          { path: 'admin/failover', element: <AdminFailoverPage /> },
        ],
      },

      // ============ Student Portal ============
      {
        element: (
          <StudentGuard>
            <StudentLayout />
          </StudentGuard>
        ),
        children: [
          { path: 'student', element: <StudentDashboardPage /> },
          { path: 'student/profile', element: <StudentProfilePage /> },
          { path: 'student/class-sections', element: <StudentClassSectionsPage /> },
          { path: 'student/enrollments', element: <StudentEnrollmentsPage /> },
          { path: 'student/schedule', element: <StudentSchedulePage /> },
        ],
      },

      // ============ Teacher Portal ============
      {
        element: (
          <TeacherGuard>
            <TeacherLayout />
          </TeacherGuard>
        ),
        children: [
          { path: 'teacher', element: <TeacherDashboardPage /> },
          { path: 'teacher/profile', element: <TeacherProfilePage /> },
          { path: 'teacher/class-sections', element: <TeacherClassSectionsPage /> },
          { path: 'teacher/schedule', element: <TeacherSchedulePage /> },
        ],
      },

      // Default redirect for any authenticated path not matched above
      { path: '/', element: <Navigate to="/student" replace /> },
    ],
  },

  { path: '*', element: <NotFoundPage /> },
]);

export { router };

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
