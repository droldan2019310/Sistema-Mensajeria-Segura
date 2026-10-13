import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { createHash, randomBytes } from "node:crypto";
import { readFile } from "node:fs/promises";

// React Refresh inserta este script en el HTML durante el desarrollo.
// Su hash permite ejecutarlo sin habilitar todos los scripts inline.
const reactRefreshScript = `import { injectIntoGlobalHook } from "/@react-refresh";
injectIntoGlobalHook(window);
window.$RefreshReg$ = () => {};
window.$RefreshSig$ = () => (type) => type;`;
const reactRefreshHash = createHash("sha256")
  .update(reactRefreshScript)
  .digest("base64");

function contentSecurityPolicy(nonce) {
  return [
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    `script-src 'self' 'sha256-${reactRefreshHash}'`,
    `style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' data:",
    "font-src 'self' data:",
    "connect-src 'self' ws://localhost:18473 ws://127.0.0.1:18473"
  ].join("; ");
}

function cspConNonce() {
  return {
    name: "csp-con-nonce",
    configureServer(server) {
      server.middlewares.use(async (request, response, next) => {
        const ruta = request.url?.split("?")[0];
        if (request.method !== "GET" || (ruta !== "/" && ruta !== "/index.html")) {
          return next();
        }

        try {
          const nonce = randomBytes(16).toString("base64");
          const fuente = await readFile(new URL("./index.html", import.meta.url), "utf8");
          const html = await server.transformIndexHtml(ruta, fuente);
          const htmlConNonce = html.replace(
            "</head>",
            `  <meta property="csp-nonce" nonce="${nonce}" />\n  </head>`
          );

          response.setHeader("Content-Type", "text/html; charset=utf-8");
          response.setHeader("Content-Security-Policy", contentSecurityPolicy(nonce));
          response.setHeader("X-Content-Type-Options", "nosniff");
          response.end(htmlConNonce);
        } catch (error) {
          next(error);
        }
      });
    }
  };
}

export default defineConfig({
  plugins: [react(), cspConNonce()],
  server: {
    host: "0.0.0.0",
    port: 18473,
    cors: false,
    headers: {
      "X-Content-Type-Options": "nosniff"
    },
    proxy: {
      "/auth": "http://localhost:17841",
      "/users": "http://localhost:17841",
      "/messages": "http://localhost:17841",
      "/groups": "http://localhost:17841",
      "/blockchain": "http://localhost:17841",
      "/contacts": "http://localhost:17841",
      "/salud": "http://localhost:17841"
    }
  }
});
