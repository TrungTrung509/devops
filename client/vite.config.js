import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        includePaths: [path.resolve(__dirname, './src')],
      },
    },
  },
  server: {
    port: 3000,
    host: true,          // Bind 0.0.0.0 — bắt buộc khi chạy trong Docker
  },
  // server: {
  //   port: 3000,
  //   proxy: {
  //     '/auth': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/users': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/branches': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/departments': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/semesters': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/students': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/teachers': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/courses': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/classrooms': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/class-sections': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/enrollments': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/failover': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //     '/health': {
  //       target: 'http://localhost:8000',
  //       changeOrigin: true,
  //     },
  //   },
  // },
})
