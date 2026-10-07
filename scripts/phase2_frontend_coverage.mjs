import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const output = join(root, "artifacts", "fase2");
mkdirSync(output, { recursive: true });

execFileSync(process.execPath, [
  join(root, "src", "frontend", "node_modules", "c8", "bin", "c8.js"),
  "--reporter=lcov",
  "--reporter=text",
  "--include=src/frontend/vite.config.js",
  `--reports-dir=${output}`,
  process.execPath,
  "--test",
  "src/frontend/tests/security-headers.test.mjs",
  "src/frontend/tests/vite-file-read.test.mjs"
], { cwd: root, stdio: "inherit" });

const report = readFileSync(join(output, "lcov.info"), "utf8")
  .replaceAll("SF:src\\frontend\\vite.config.js", "SF:src/frontend/vite.config.js");
writeFileSync(join(output, "frontend-lcov.info"), report);
