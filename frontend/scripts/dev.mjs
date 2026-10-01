import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';

const server = await createServer({
  root: process.cwd(),
  configFile: false,
  plugins: [vue()],
  server: { host: '127.0.0.1', port: 5183, strictPort: true, proxy: { '/api': 'http://127.0.0.1:4183' } }
});
await server.listen();
server.printUrls();
