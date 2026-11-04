/* Post-process tsc output so Node ESM can run it for the jsdom smoke:
   add .js to relative imports, drop the CSS import (vite handles it). */
import { copyFileSync, readFileSync, writeFileSync } from "node:fs";
import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";

copyFileSync("src/styles.css", "static-build/styles.css");
copyFileSync("public/veytac-logo.svg", "static-build/veytac-logo.svg");

function jsFiles(dir) {
  const out = [];
  for (const e of readdirSync(dir)) {
    if (e === "vendor") continue;
    const p = join(dir, e);
    if (statSync(p).isDirectory()) out.push(...jsFiles(p));
    else if (e.endsWith(".js")) out.push(p);
  }
  return out;
}

for (const f of jsFiles("static-build")) {
  let src = readFileSync(f, "utf8");
  src = src
    .replaceAll('from "./styles.css";', "/* styles.css: served by vite */")
    .replaceAll('import "./styles.css";', "/* styles.css: served by vite */");
  src = src
    .replaceAll(/from "(\.[^"]*)";/g, 'from "$1.js";')
    .replaceAll(/from '(\.[^']*)';/g, "from '$1.js';");
  writeFileSync(f, src);
}
console.log("patched static build for node ESM");
