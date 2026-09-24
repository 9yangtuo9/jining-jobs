import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  // GitHub Pages 部署在 /jining-jobs/ 子路径下（构建时传 --mode ghpages），其他环境用根路径
  base: mode === 'ghpages' ? '/jining-jobs/' : '/',
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
}))
