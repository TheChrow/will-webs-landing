// Genera la Content-Security-Policy del sitio estático con los hashes SHA-256 de los
// <script> inline que React Router incrusta en cada HTML pre-renderizado.
// Así la CSP no necesita 'unsafe-inline'. Uso: node scripts/csp.mjs build/client out/csp.conf
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const [root = "build/client", out = "build/csp.conf"] = process.argv.slice(2);

function* htmlFiles(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* htmlFiles(path);
    else if (name.endsWith(".html")) yield path;
  }
}

const INLINE_SCRIPT = /<script(?![^>]*\bsrc=)([^>]*)>([\s\S]*?)<\/script>/gi;
const hashes = new Set();
let files = 0;

for (const file of htmlFiles(root)) {
  files += 1;
  const html = readFileSync(file, "utf8");
  for (const [, attrs, body] of html.matchAll(INLINE_SCRIPT)) {
    // Bloques de datos (JSON-LD) no se ejecutan: no requieren hash.
    if (/type=["']?application\/(ld\+)?json/i.test(attrs)) continue;
    if (!body.trim()) continue;
    hashes.add(`'sha256-${createHash("sha256").update(body, "utf8").digest("base64")}'`);
  }
}

const TURNSTILE = "https://challenges.cloudflare.com";
const policy = [
  "default-src 'self'",
  `script-src 'self' ${[...hashes].sort().join(" ")} ${TURNSTILE}`,
  "style-src 'self'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'self'",
  `frame-src ${TURNSTILE}`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "upgrade-insecure-requests",
].join("; ");

writeFileSync(out, `add_header Content-Security-Policy "${policy}" always;\n`);
console.log(`CSP: ${hashes.size} hashes de scripts inline en ${files} archivos HTML -> ${out}`);
