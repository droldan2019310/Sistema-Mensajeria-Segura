import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { createServer } from "vite";
import { fileURLToPath } from "node:url";
import config from "../vite.config.js";

test("La configuración mantiene CORS y cabeceras de seguridad", () => {
  assert.equal(config.server.cors, false);
  assert.equal(config.server.headers["X-Content-Type-Options"], "nosniff");
  assert.equal(config.server.headers["X-Frame-Options"], "DENY");
  assert.ok(config.server.headers["Content-Security-Policy"].includes("default-src 'none'"));
  assert.ok(config.server.headers["Content-Security-Policy"].includes("form-action 'none'"));
});

test("El middleware protege HTML y deja pasar otras rutas", async () => {
  const plugin = config.plugins.find((item) => item.name === "csp-con-nonce");
  let middleware;
  plugin.configureServer({
    middlewares: { use: (handler) => { middleware = handler; } },
    transformIndexHtml: async (_ruta, html) => html
  });

  const headers = new Map();
  let body;
  const response = {
    setHeader: (name, value) => headers.set(name.toLowerCase(), value),
    end: (value) => { body = value; }
  };
  await middleware({ method: "GET", url: "/?x=1" }, response, () => {
    throw new Error("La página principal no debe omitir las cabeceras");
  });
  const nonce = body.match(/nonce="([^"]+)"/)?.[1];
  assert.ok(nonce);
  assert.equal(headers.get("x-frame-options"), "DENY");
  assert.equal(headers.get("x-content-type-options"), "nosniff");
  assert.ok(headers.get("content-security-policy").includes(`'nonce-${nonce}'`));

  let pasó = false;
  await middleware({ method: "POST", url: "/" }, response, () => { pasó = true; });
  assert.equal(pasó, true);
  pasó = false;
  await middleware({ method: "GET", url: "/src/main.jsx" }, response, () => { pasó = true; });
  assert.equal(pasó, true);
});

async function withDevServer(run) {
  const server = await createServer({
    root: fileURLToPath(new URL("../", import.meta.url)),
    logLevel: "silent",
    server: { host: "127.0.0.1", port: 0, strictPort: true }
  });

  try {
    await server.listen();
    const port = server.httpServer.address().port;
    await run(`http://127.0.0.1:${port}`);
  } finally {
    await server.close();
  }
}

test("Vite no autoriza solicitudes desde otro origen local", async () => {
  await withDevServer(async (url) => {
    for (const ruta of ["/", "/src/main.jsx"]) {
      const respuesta = await fetch(`${url}${ruta}`, {
        headers: { Origin: "http://localhost:9999" }
      });

      assert.equal(respuesta.status, 200);
      assert.equal(respuesta.headers.get("access-control-allow-origin"), null);
    }
  });
});

test("Vite entrega CSP y nosniff sin bloquear el script de React Refresh", async () => {
  await withDevServer(async (url) => {
    const respuesta = await fetch(url);
    const html = await respuesta.text();
    const csp = respuesta.headers.get("content-security-policy");
    const nonce = html.match(/<meta property="csp-nonce" nonce="([^"]+)"\s*\/>/)?.[1];

    assert.equal(respuesta.status, 200);
    assert.equal(respuesta.headers.get("x-content-type-options"), "nosniff");
    assert.ok(csp?.includes("frame-ancestors 'none'"));
    assert.ok(csp.includes("script-src 'self' 'sha256-"));
    assert.ok(nonce, "El HTML debe entregar el nonce a Vite");
    assert.ok(csp.includes(`style-src 'self' 'nonce-${nonce}'`));
    assert.equal(csp.includes("'unsafe-inline'"), false);

    const scriptsInline = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)]
      .map((coincidencia) => coincidencia[1])
      .filter(Boolean);
    assert.ok(scriptsInline.length > 0, "React Refresh debe aparecer en el HTML");

    for (const script of scriptsInline) {
      const hash = createHash("sha256").update(script).digest("base64");
      assert.ok(csp.includes(`'sha256-${hash}'`), "La CSP debe permitir el script generado por Vite");
    }

    const modulo = await fetch(`${url}/src/main.jsx`);
    assert.equal(modulo.status, 200);
    assert.equal(modulo.headers.get("x-content-type-options"), "nosniff");

    const otraRespuesta = await fetch(url);
    const otroNonce = (await otraRespuesta.text())
      .match(/<meta property="csp-nonce" nonce="([^"]+)"\s*\/>/)?.[1];
    assert.ok(otroNonce);
    assert.notEqual(otroNonce, nonce, "Cada respuesta debe tener un nonce nuevo");

    const index = await fetch(`${url}/index.html`);
    assert.equal(index.status, 200);
    assert.ok(index.headers.get("content-security-policy")?.includes("frame-ancestors 'none'"));
  });
});

test("Vite bloquea la carga del frontend en marcos ajenos", async () => {
  await withDevServer(async (url) => {
    for (const ruta of ["/", "/index.html"]) {
      const respuesta = await fetch(`${url}${ruta}`);
      assert.equal(respuesta.headers.get("x-frame-options"), "DENY");
      assert.ok(
        respuesta.headers.get("content-security-policy")?.includes("frame-ancestors 'none'")
      );
    }
  });
});

test("Los recursos estáticos reciben una CSP restrictiva", async () => {
  await withDevServer(async (url) => {
    const respuesta = await fetch(`${url}/sitemap.xml`);
    assert.equal(respuesta.status, 200);
    assert.ok(respuesta.headers.get("content-security-policy")?.includes("default-src 'none'"));
    assert.ok(respuesta.headers.get("content-security-policy")?.includes("form-action 'none'"));
    assert.equal(respuesta.headers.get("x-content-type-options"), "nosniff");
  });
});
