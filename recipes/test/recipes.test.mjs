// Runs each recipe against a local fixture site with a passing and a failing case.
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

const here = fileURLToPath(new URL(".", import.meta.url));
const recipes = join(here, "..");
const site = join(here, "site");
const work = mkdtempSync(join(tmpdir(), "recipes-"));
let server;
let base;

before(async () => {
  server = createServer((req, res) => {
    const path = new URL(req.url, "http://x").pathname;
    if (path === "/api/me") {
      const ok = req.headers.authorization === "Bearer t0ken";
      res.writeHead(ok ? 200 : 401, { "content-type": "application/json" });
      return res.end(JSON.stringify(ok ? { user: { id: 7, name: "Ana" } } : { error: "unauthorized" }));
    }
    if (path === "/api/slow") return setTimeout(() => { res.writeHead(200); res.end("{}"); }, 400);
    if (path === "/api/html") { res.writeHead(200, { "content-type": "text/html" }); return res.end("<h1>oops</h1>"); }
    const file = join(site, path === "/" ? "good.html" : path.slice(1));
    if (!file.startsWith(site) || !existsSync(file)) { res.writeHead(404); return res.end("not found"); }
    res.writeHead(200, { "content-type": "text/html" });
    res.end(readFileSync(file));
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => server.close());

function run(script, args, env = {}) {
  return new Promise((resolve) => {
    execFile(process.execPath, [join(recipes, script), ...args], { cwd: work, env: { ...process.env, ...env } },
      (error, stdout, stderr) => resolve({ code: error ? error.code : 0, stdout, stderr }));
  });
}

test("api-check passes on a good response", async () => {
  const r = await run("api-check.mjs", ["--url", `${base}/api/me`, "--bearer-env", "TOKEN",
    "--json-has", "user.id", "--json-has", "user.name", "--max-ms", "2000"], { TOKEN: "t0ken" });
  assert.equal(r.code, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /CHECKED  ok    JSON has user\.id/);
  assert.match(r.stdout, /NOT CHECKED/);
  assert.doesNotMatch(r.stdout + r.stderr, /t0ken/);
});

test("api-check fails on status, missing field, non-JSON, and slowness", async () => {
  const auth = await run("api-check.mjs", ["--url", `${base}/api/me`, "--json-has", "user.id"]);
  assert.equal(auth.code, 1);
  assert.match(auth.stdout, /FAIL  status is 200 — got 401/);
  assert.match(auth.stdout, /FAIL  JSON has user\.id — missing/);
  const html = await run("api-check.mjs", ["--url", `${base}/api/html`, "--json-has", "x"]);
  assert.match(html.stdout, /FAIL  body is JSON/);
  const slow = await run("api-check.mjs", ["--url", `${base}/api/slow`, "--max-ms", "100"]);
  assert.equal(slow.code, 1);
  assert.match(slow.stdout, /FAIL  responds within 100 ms — took \d+ ms/);
  const down = await run("api-check.mjs", ["--url", "http://127.0.0.1:9/none"]);
  assert.equal(down.code, 1);
  assert.match(down.stdout, /FAIL  GET .* responds/);
});

test("api-check usage errors exit 2", async () => {
  assert.equal((await run("api-check.mjs", [])).code, 2);
  assert.equal((await run("api-check.mjs", ["--url", `${base}/api/me`, "--bearer-env", "UNSET_VAR_X"])).code, 2);
});

const loginSteps = [
  { goto: "/login.html" },
  { fill: "#email", value: "ana@example.com" },
  { fill: "#password", env: "APP_PASSWORD" },
  { click: "text=Sign in" },
  { expectUrl: "/welcome.html" },
  { expectText: "Welcome back" },
];

test("browser-flow walks a login flow without printing the secret", async () => {
  const steps = join(work, "login.json");
  writeFileSync(steps, JSON.stringify(loginSteps));
  const r = await run("browser-flow.mjs", ["--url", base, "--steps", steps], { APP_PASSWORD: "s3cret" });
  assert.equal(r.code, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /step 3: fill #password with value from \$APP_PASSWORD/);
  assert.match(r.stdout, /browser-flow: PASS/);
  assert.doesNotMatch(r.stdout + r.stderr, /s3cret/);
});

test("browser-flow stops at the failing step, screenshots, and lists skipped steps", async () => {
  const steps = join(work, "login.json");
  writeFileSync(steps, JSON.stringify(loginSteps));
  const shot = join(work, "fail.png");
  const r = await run("browser-flow.mjs", ["--url", base, "--steps", steps, "--timeout", "1500", "--screenshot", shot],
    { APP_PASSWORD: "wrong-pass" });
  assert.equal(r.code, 1);
  assert.match(r.stdout, /FAIL  step 5: URL contains \/welcome\.html — not done within 1500 ms/);
  assert.match(r.stdout, /NOT CHECKED     1 later step\(s\)/);
  assert.ok(existsSync(shot));
  assert.doesNotMatch(r.stdout + r.stderr, /wrong-pass/);
  const missing = await run("browser-flow.mjs", ["--url", base, "--steps", steps]);
  assert.equal(missing.code, 2);
  assert.match(missing.stderr, /APP_PASSWORD is not set/);
});

test("responsive passes a fluid page and names the element that overflows", async () => {
  const good = await run("responsive.mjs", ["--url", `${base}/good.html`, "--visible", "#buy", "--visible", "nav"]);
  assert.equal(good.code, 0, good.stdout + good.stderr);
  assert.match(good.stdout, /375px: no horizontal scroll/);
  const bad = await run("responsive.mjs", ["--url", `${base}/bad.html`, "--widths", "375,1280", "--visible", "#buy"]);
  assert.equal(bad.code, 1);
  assert.match(bad.stdout, /FAIL  375px: no horizontal scroll — page is \d+px wide; widest: div#promo\.banner/);
  assert.match(bad.stdout, /ok    1280px: no horizontal scroll/);
  assert.match(bad.stdout, /FAIL  375px: #buy is visible — hidden or missing/);
});

test("a11y-basics passes a clean page and names each gap on a broken one", async () => {
  const good = await run("a11y-basics.mjs", ["--url", `${base}/good.html`]);
  assert.equal(good.code, 0, good.stdout + good.stderr);
  assert.match(good.stdout, /NOT CHECKED     colour contrast/);
  const bad = await run("a11y-basics.mjs", ["--url", `${base}/bad.html`]);
  assert.equal(bad.code, 1);
  for (const gap of [/FAIL  page declares a language/, /FAIL  page has a title/, /FAIL  every image has an alt attribute/,
    /FAIL  every form field has a label .* 1: <input id="email"/, /FAIL  every button and link has an accessible name .* 2:/,
    /FAIL  ids are unique — #dup ×2/]) {
    assert.match(bad.stdout, gap);
  }
});
