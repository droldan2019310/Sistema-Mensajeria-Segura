import assert from "node:assert/strict";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { tmpdir } from "node:os";
import test from "node:test";
import { createServer } from "vite";

test("Vite no entrega un archivo externo con ?import&raw??", async () => {
  const marker = `FASE2-SENTINEL-${randomUUID()}`;
  const testDir = await mkdtemp(path.join(tmpdir(), "vite-fase2-"));
  const filePath = path.join(testDir, "sentinel.txt");
  let server;

  await writeFile(filePath, marker, "utf8");

  try {
    server = await createServer({
      logLevel: "silent",
      server: { host: "127.0.0.1", port: 0, strictPort: true }
    });
    await server.listen();

    const port = server.httpServer.address().port;
    const fileUrl = `/@fs/${filePath.replaceAll("\\", "/")}`;
    const normal = await fetch(`http://127.0.0.1:${port}${fileUrl}`);
    const normalBody = await normal.text();
    const bypass = await fetch(`http://127.0.0.1:${port}${fileUrl}?import&raw??`);
    const bypassBody = await bypass.text();

    assert.equal(normalBody.includes(marker), false, "El acceso normal ya debe estar bloqueado");
    assert.equal(bypassBody.includes(marker), false, `La variante vulnerable entregó el archivo (HTTP ${bypass.status})`);
  } finally {
    await server?.close();
    await rm(testDir, { recursive: true, force: true });
  }
});
