import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // 相对路径 base：同一份构建产物既能在本地后端托管（/）使用，
  // 也能直接部署到 GitHub Pages 子路径（/ask-my-resume/）
  base: './',
})
