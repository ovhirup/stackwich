#!/usr/bin/env node
// Walk one user flow in Chromium from a JSON list of steps.
//
//   node browser-flow.mjs --url http://localhost:3000 --steps login.json
//
// Steps: {"goto": "/login"}, {"fill": "#email", "value": "a@b.c"},
// {"fill": "#password", "env": "APP_PASSWORD"}, {"click": "text=Sign in"},
// {"expectText": "Welcome"}, {"expectUrl": "/dashboard"}.
// Values from "env" are read from the environment and never printed.

import { readFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { chromium } from "playwright";
import { Report, usage } from "./lib.mjs";

const { values } = parseArgs({
  options: {
    url: { type: "string" },
    steps: { type: "string" },
    screenshot: { type: "string", default: "flow-failure.png" },
    timeout: { type: "string", default: "10000" },
  },
});
if (!values.url || !values.steps) usage("browser-flow: --url and --steps are required");

let steps;
try {
  steps = JSON.parse(readFileSync(values.steps, "utf8"));
} catch (error) {
  usage(`browser-flow: cannot read steps: ${error.message}`);
}
if (!Array.isArray(steps) || !steps.length) usage("browser-flow: steps must be a non-empty JSON array");
for (const step of steps) {
  if (step.env && process.env[step.env] === undefined) usage(`browser-flow: environment variable ${step.env} is not set`);
}

const timeout = Number(values.timeout);
const report = new Report("browser-flow");
const browser = await chromium.launch();
const page = await browser.newPage();
page.setDefaultTimeout(timeout);

function describe(step) {
  if (step.goto !== undefined) return `go to ${step.goto}`;
  if (step.fill !== undefined) {
    const source = step.env ? `value from $${step.env}` : `${String(step.value ?? "").length}-character value`;
    return `fill ${step.fill} with ${source}`;
  }
  if (step.click !== undefined) return `click ${step.click}`;
  if (step.expectText !== undefined) return `page shows "${step.expectText}"`;
  if (step.expectUrl !== undefined) return `URL contains ${step.expectUrl}`;
  return `unknown step ${JSON.stringify(Object.keys(step))}`;
}

async function perform(step) {
  if (step.goto !== undefined) await page.goto(new URL(step.goto, values.url).href);
  else if (step.fill !== undefined) await page.fill(step.fill, step.env ? process.env[step.env] : String(step.value ?? ""));
  else if (step.click !== undefined) await page.click(step.click);
  else if (step.expectText !== undefined) await page.getByText(step.expectText).first().waitFor({ state: "visible" });
  else if (step.expectUrl !== undefined) await page.waitForURL((url) => url.href.includes(step.expectUrl));
  else throw new Error("unknown step");
}

let stopped = false;
for (const [index, step] of steps.entries()) {
  const what = `step ${index + 1}: ${describe(step)}`;
  if (stopped) continue;
  try {
    await perform(step);
    report.pass(what);
  } catch (error) {
    const reason = error.name === "TimeoutError" ? `not done within ${timeout} ms` : error.message.split("\n")[0];
    report.fail(what, `${reason}; page was ${page.url()}`);
    await page.screenshot({ path: values.screenshot, fullPage: true });
    report.lines.push(`         screenshot: ${values.screenshot}`);
    stopped = true;
  }
}
const skipped = stopped ? steps.length - report.lines.filter((l) => l.startsWith("CHECKED")).length : 0;
await browser.close();
report.finish([
  ...(skipped ? [`${skipped} later step(s), because an earlier step failed`] : []),
  "other paths through the app, and error handling off this path",
  "visual appearance; text was found, not judged",
  "browsers other than Chromium",
]);
