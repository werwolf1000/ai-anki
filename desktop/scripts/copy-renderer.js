// Копирует сборку web/dist в desktop/renderer (её грузит Electron по протоколу app://)
const fs = require("fs");
const path = require("path");

const src = path.resolve(__dirname, "../../web/dist");
const dst = path.resolve(__dirname, "../renderer");
if (!fs.existsSync(path.join(src, "index.html"))) {
  console.error("Нет web/dist/index.html — сначала соберите фронтенд");
  process.exit(1);
}
fs.rmSync(dst, { recursive: true, force: true });
fs.cpSync(src, dst, { recursive: true });
console.log(`renderer: ${src} -> ${dst}`);
