#!/usr/bin/env node
// Check one HTTP endpoint: status, required JSON fields, and response time.
//
//   node api-check.mjs --url https://example.com/api/me --status 200 \
//     --json-has user.id --max-ms 800 --bearer-env API_TOKEN

import { parseArgs } from "node:util";
import { Report, usage } from "./lib.mjs";

const { values } = parseArgs({
  options: {
    url: { type: "string" },
    method: { type: "string", default: "GET" },
    status: { type: "string", default: "200" },
    "json-has": { type: "string", multiple: true, default: [] },
    "max-ms": { type: "string" },
    "bearer-env": { type: "string" },
  },
});
if (!values.url) usage("api-check: --url is required");

const headers = {};
if (values["bearer-env"]) {
  const token = process.env[values["bearer-env"]];
  if (!token) usage(`api-check: environment variable ${values["bearer-env"]} is not set`);
  headers.Authorization = `Bearer ${token}`;
}

function lookup(data, path) {
  return path.split(".").reduce((node, key) => (node != null && typeof node === "object" ? node[key] : undefined), data);
}

const report = new Report("api-check");
const started = performance.now();
let response;
try {
  response = await fetch(values.url, { method: values.method, headers });
} catch (error) {
  report.fail(`${values.method} ${values.url} responds`, error.cause?.code || error.message);
  report.finish(["anything else: the request did not complete"]);
}
const elapsed = Math.round(performance.now() - started);
const body = await response.text();

report.check(String(response.status) === values.status, `status is ${values.status}`, `got ${response.status}`);
if (values["max-ms"]) {
  report.check(elapsed <= Number(values["max-ms"]), `responds within ${values["max-ms"]} ms`, `took ${elapsed} ms`);
}
if (values["json-has"].length) {
  let data;
  try {
    data = JSON.parse(body);
    report.pass("body is JSON");
  } catch {
    report.fail("body is JSON", `starts with ${JSON.stringify(body.slice(0, 60))}`);
  }
  for (const path of values["json-has"]) {
    if (data !== undefined) report.check(lookup(data, path) !== undefined, `JSON has ${path}`, "missing");
  }
}
report.finish([
  "other endpoints, methods, or inputs",
  "field values and types beyond presence",
  "side effects on stored data",
  "behavior under load; one request was timed, not a benchmark",
]);
