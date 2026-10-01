import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? '/coffee-flavor-atlas/' : '/',
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5183,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:4183',
      '/media': 'http://127.0.0.1:4183'
    }
  },
  preview: { host: '127.0.0.1', port: 5184, strictPort: true, proxy: { '/api': 'http://127.0.0.1:4183', '/media': 'http://127.0.0.1:4183' } }
});
