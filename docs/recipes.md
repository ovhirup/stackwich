# Acceptance-check recipes

Unit tests can pass while the thing a user sees is broken: a form that never submits, a layout
that scrolls sideways on a phone, an API that drops a field. And many projects built with AI
agents have no tests at all, which leaves the verifier nothing real to run.

`recipes/` has four small checks a verifier can run as its verification command. Each prints
what it checked, what failed, and what it did **not** check, then exits 0 on pass, 1 on fail,
and 2 on a usage error. They need Node.js 20 or newer; the three browser recipes use Chromium
through Playwright.

## Set up once

```bash
cd ~/stackwich-tools/recipes
npm ci
npx playwright install chromium
```

## The recipes

### API: `api-check.mjs`

```bash
node api-check.mjs --url https://staging.example.com/api/me --status 200 \
  --json-has user.id --json-has user.email --max-ms 800 --bearer-env API_TOKEN
```

Checks one request's status, that each `--json-has` path exists, and the response time. A token
is read from the named environment variable and never printed.

### Browser flow: `browser-flow.mjs`

```bash
APP_PASSWORD=… node browser-flow.mjs --url http://localhost:3000 --steps login.json
```

`login.json` lists the steps in order:

```json
[
  {"goto": "/login"},
  {"fill": "#email", "value": "test@example.com"},
  {"fill": "#password", "env": "APP_PASSWORD"},
  {"click": "text=Sign in"},
  {"expectUrl": "/dashboard"},
  {"expectText": "Welcome back"}
]
```

Supported steps are `goto`, `fill` (with `value`, or `env` for anything secret), `click`,
`expectText`, and `expectUrl`. The recipe stops at the first failing step, saves a full-page
screenshot (`--screenshot`, default `flow-failure.png`), and lists the steps it skipped. Typed
values are never printed: a step shows only its length or the variable it came from. Use a test
account, never a real one.

### Responsive layout: `responsive.mjs`

```bash
node responsive.mjs --url http://localhost:3000 --widths 375,768,1280 --visible nav --visible "#buy"
```

At each width it checks that the page does not scroll sideways, and names the widest
elements if it does. Each `--visible` selector must be visible at every width.

### Accessibility basics: `a11y-basics.mjs`

```bash
node a11y-basics.mjs --url http://localhost:3000
```

Checks for a page language, a title, images without `alt`, form fields without labels, buttons
and links without an accessible name, and duplicate ids. It names up to three examples of each.

**This is a smoke test, not an accessibility audit.** It does not check colour contrast, keyboard
access, focus order, what a screen reader announces, or content that appears after load. Use an
audit tool such as axe-core and test by hand before claiming a page is accessible.

## Example output

Recorded on 2026-10-31 against the test fixtures in `recipes/test/site/`:

```text
$ node a11y-basics.mjs --url http://127.0.0.1:8765/bad.html
CHECKED  FAIL  page declares a language (<html lang>) — missing
CHECKED  FAIL  page has a title — empty or missing
CHECKED  FAIL  every image has an alt attribute (empty alt is fine for decoration) — 1: <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
CHECKED  FAIL  every form field has a label — 1: <input id="email" type="email">
CHECKED  FAIL  every button and link has an accessible name — 2: <button></button> | <a href="#"></a>
CHECKED  FAIL  ids are unique — #dup ×2
NOT CHECKED     colour contrast
NOT CHECKED     keyboard access and focus order
NOT CHECKED     what a screen reader actually announces, and ARIA validity
NOT CHECKED     content added after load, other pages, and dynamic states
NOT CHECKED     for a full review use an audit tool such as axe-core plus manual testing
a11y-basics: FAIL (6 failed)

$ node responsive.mjs --url http://127.0.0.1:8765/bad.html --widths 375,1280
CHECKED  FAIL  375px: no horizontal scroll — page is 1208px wide; widest: div#promo.banner (1208px)
CHECKED  ok    1280px: no horizontal scroll
NOT CHECKED     how the page looks: spacing, overlap, font sizes, and images
NOT CHECKED     page heights, scrolling content, and states after interaction
NOT CHECKED     other pages, and real devices or browsers other than Chromium
responsive: FAIL (1 failed)
```

## Using them as the gate

Give the verifier the recipe as its verification command, with the expected result, for example:

> Verify with `node ~/stackwich-tools/recipes/browser-flow.mjs --url http://localhost:3000
> --steps checks/login.json`; expect `browser-flow: PASS`.

To bind the verdict to the files it tested, run the recipe through
[verification records](verify-gate.md):

```bash
python3 ~/stackwich-tools/tools/verify_gate.py run -- node ~/stackwich-tools/recipes/responsive.mjs --url http://localhost:3000
```

The app has to be running for the browser and API recipes, and they check whatever is running at
that URL. A pass says these specific checks passed against that server at that moment; it says
nothing about the pages, paths, and properties listed under NOT CHECKED.

## Tests

`recipes/test/recipes.test.mjs` runs every recipe against a local fixture site with a passing and
a failing page, and checks that secrets never appear in the output. CI runs it in its own job:

```bash
cd recipes && npm ci && npx playwright install --with-deps chromium && npm test
```
