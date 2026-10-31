// Shared reporting for the acceptance-check recipes. Every recipe prints what it
// checked, what failed, and what it did not check, then exits 0 (pass) or 1 (fail).

export class Report {
  constructor(name) {
    this.name = name;
    this.lines = [];
    this.failed = 0;
  }

  pass(what) {
    this.lines.push(`CHECKED  ok    ${what}`);
  }

  fail(what, detail = "") {
    this.failed += 1;
    this.lines.push(`CHECKED  FAIL  ${what}${detail ? ` — ${detail}` : ""}`);
  }

  check(ok, what, detail = "") {
    if (ok) this.pass(what);
    else this.fail(what, detail);
    return ok;
  }

  finish(notChecked) {
    for (const line of this.lines) console.log(line);
    for (const item of notChecked) console.log(`NOT CHECKED     ${item}`);
    console.log(`${this.name}: ${this.failed ? `FAIL (${this.failed} failed)` : "PASS"}`);
    process.exit(this.failed ? 1 : 0);
  }
}

// Usage errors exit 2, so a broken invocation is never mistaken for a failed check.
export function usage(message) {
  console.error(message);
  process.exit(2);
}
