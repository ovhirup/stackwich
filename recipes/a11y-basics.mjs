#!/usr/bin/env node
// Check a page for common, mechanically detectable accessibility gaps.
// This is a smoke test, not an accessibility audit.
//
//   node a11y-basics.mjs --url http://localhost:3000

import { parseArgs } from "node:util";
import { chromium } from "playwright";
import { Report, usage } from "./lib.mjs";

const { values } = parseArgs({ options: { url: { type: "string" } } });
if (!values.url) usage("a11y-basics: --url is required");

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(values.url, { waitUntil: "load" });
const found = await page.evaluate(() => {
  const describe = (el) => {
    const html = el.outerHTML.replace(/\s+/g, " ");
    return html.length > 70 ? `${html.slice(0, 67)}...` : html;
  };
  const byIds = (ids) => (ids || "").split(/\s+/).filter(Boolean)
    .map((id) => document.getElementById(id)?.textContent.trim() || "").join(" ").trim();
  const named = (el) => Boolean(
    el.getAttribute("aria-label")?.trim() || byIds(el.getAttribute("aria-labelledby")) ||
    el.getAttribute("title")?.trim() || el.textContent.trim() ||
    [...el.querySelectorAll("img[alt]")].some((img) => img.alt.trim()));
  const labelled = (el) => Boolean(
    (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.textContent.trim()) ||
    el.closest("label")?.textContent.trim() || el.getAttribute("aria-label")?.trim() ||
    byIds(el.getAttribute("aria-labelledby")) || el.getAttribute("title")?.trim());
  const fields = [...document.querySelectorAll("input, select, textarea")]
    .filter((el) => !["hidden", "submit", "button", "reset", "image"].includes(el.type));
  const counts = {};
  for (const el of document.querySelectorAll("[id]")) counts[el.id] = (counts[el.id] || 0) + 1;
  return {
    lang: document.documentElement.getAttribute("lang")?.trim() || "",
    title: document.title.trim(),
    images: [...document.querySelectorAll("img:not([alt])")].map(describe),
    fields: fields.filter((el) => !labelled(el)).map(describe),
    controls: [...document.querySelectorAll("button, a[href], [role=button]")].filter((el) => !named(el)).map(describe),
    ids: Object.entries(counts).filter(([, n]) => n > 1).map(([id, n]) => `#${id} ×${n}`),
  };
});
await browser.close();

const examples = (items) => `${items.length}: ${items.slice(0, 3).join(" | ")}${items.length > 3 ? " | ..." : ""}`;
const report = new Report("a11y-basics");
report.check(Boolean(found.lang), "page declares a language (<html lang>)", "missing");
report.check(Boolean(found.title), "page has a title", "empty or missing");
report.check(!found.images.length, "every image has an alt attribute (empty alt is fine for decoration)", examples(found.images));
report.check(!found.fields.length, "every form field has a label", examples(found.fields));
report.check(!found.controls.length, "every button and link has an accessible name", examples(found.controls));
report.check(!found.ids.length, "ids are unique", found.ids.join(", "));
report.finish([
  "colour contrast",
  "keyboard access and focus order",
  "what a screen reader actually announces, and ARIA validity",
  "content added after load, other pages, and dynamic states",
  "for a full review use an audit tool such as axe-core plus manual testing",
]);
