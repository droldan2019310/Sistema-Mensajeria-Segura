import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { createServer } from "vite";

async function withDevServer(run) {
  const server = await createServer({
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
