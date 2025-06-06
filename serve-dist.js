// Simple static file server for testing production build
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { join, extname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const distDir = join(__dirname, 'dist');

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml'
};

const server = createServer((req, res) => {
  let filePath = join(distDir, req.url === '/' ? 'index.html' : req.url);
  
  if (!existsSync(filePath)) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }

  const ext = extname(filePath);
  const contentType = mimeTypes[ext] || 'application/octet-stream';
  
  res.writeHead(200, { 'Content-Type': contentType });
  res.end(readFileSync(filePath));
});

const port = 3000;
server.listen(port, () => {
  console.log(`🚀 Production build running at http://localhost:${port}`);
  console.log('This simulates the desktop app performance');
});