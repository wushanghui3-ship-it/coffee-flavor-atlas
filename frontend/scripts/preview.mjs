import { createServer, preview } from 'vite';
import vue from '@vitejs/plugin-vue';

const server = await preview({ root: process.cwd(), configFile: false, plugins: [vue()], preview: { host: '127.0.0.1', port: 5184, strictPort: true, proxy: { '/api': 'http://127.0.0.1:4183' } } });
server.printUrls();
