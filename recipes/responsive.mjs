#!/usr/bin/env node
// Load a page at several widths and check for horizontal overflow.
//
//   node responsive.mjs --url http://localhost:3000 --widths 375,768,1280 --visible "nav" --visible "#buy"

import { parseArgs } from "node:util";
import { chromium } from "playwright";
import { Report, usage } from "./lib.mjs";

const { values } = parseArgs({
  options: {
    url: { type: "string" },
    widths: { type: "string", default: "375,768,1280" },
    visible: { type: "string", multiple: true, default: [] },
  },
});
if (!values.url) usage("responsive: --url is required");
const widths = values.widths.split(",").map(Number);
if (widths.some((w) => !Number.isInteger(w) || w < 200)) usage("responsive: --widths takes whole pixel widths of 200 or more");

const report = new Report("responsive");
const browser = await chromium.launch();
const page = await browser.newPage();
for (const width of widths) {
  await page.setViewportSize({ width, height: 900 });
  await page.goto(values.url, { waitUntil: "load" });
  const overflow = await page.evaluate(() => {
    const limit = document.documentElement.clientWidth;
    const wide = [];
    for (const el of document.body.querySelectorAll("*")) {
      const right = el.getBoundingClientRect().right;
      if (right > limit + 1) {
        const name = el.tagName.toLowerCase() + (el.id ? `#${el.id}` : "") +
          (typeof el.className === "string" && el.className.trim() ? `.${el.className.trim().split(/\s+/).join(".")}` : "");
        wide.push(`${name} (${Math.round(right)}px)`);
      }
    }
    return { scroll: document.documentElement.scrollWidth, limit, wide: wide.slice(0, 3) };
  });
  report.check(overflow.scroll <= overflow.limit, `${width}px: no horizontal scroll`,
    `page is ${overflow.scroll}px wide; widest: ${overflow.wide.join(", ") || "unknown"}`);
  for (const selector of values.visible) {
    report.check(await page.locator(selector).first().isVisible(), `${width}px: ${selector} is visible`, "hidden or missing");
  }
}
await browser.close();
report.finish([
  "how the page looks: spacing, overlap, font sizes, and images",
  "page heights, scrolling content, and states after interaction",
  "other pages, and real devices or browsers other than Chromium",
]);
