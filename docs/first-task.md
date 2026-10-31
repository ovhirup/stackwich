# Your first verified task

About fifteen minutes from install to a verified fix, and back out again. You need Claude Code,
Python 3, and git.

This is a demonstration of the workflow on a three-line bug. It shows what the gate looks like;
it is not evidence that Stackwich improves results on real work. See
[enforcement.md](enforcement.md) for what is mechanical and what depends on the model.

The command output below is real, recorded on 2026-10-31 with Python 3.13. Temporary paths are
shortened. What Claude says in step 4 depends on the model and is described, not quoted.

## 1. Install and check

Install the plugin and run the skill, as in the [README](../README.md#install). Then clone this
repository somewhere outside your project and run the diagnostics from your project directory:

```bash
git clone https://github.com/ovhirup/stackwich ~/stackwich-tools
cd ~/my-project
python3 ~/stackwich-tools/tools/diagnose.py
```

A healthy user-level install reports `policy-rev 5`, three Stackwich agents, and
`Problems: none found`. Here is a setup with a real conflict: the project has its own agent
called `executor`, which shadows Stackwich's.

```text
Stackwich policy-rev in this checkout: 5

user (~/.claude)
  CLAUDE.md policy: installed, policy-rev 5
  agent advisor: Stackwich
  agent executor: Stackwich
  agent verifier: Stackwich

project (~/my-project/.claude)
  CLAUDE.md policy: none
  agent executor: not Stackwich

Problems:
  - agent 'executor' defined at both levels; the project definition takes precedence

For a line-by-line check of one scope, run tools/check_install.py on it.
```

Fix every problem it lists before going on; each line says what to do. The diagnostics print
names, paths, and revisions only, never file contents. For a stricter check of one scope, run
`python3 ~/stackwich-tools/tools/check_install.py ~/.claude`.

## 2. Copy the demo project

```bash
cp -r ~/stackwich-tools/examples/first-task ~/first-task
cd ~/first-task
git init -q && git add . && git commit -qm "Broken checkout total"
```

`cart.py` adds up a cart and applies a percentage discount. It has one bug.

## 3. See it fail

```text
$ python3 -m unittest
..F
======================================================================
FAIL: test_ten_percent_discount (test_cart.TotalTests.test_ten_percent_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "first-task/test_cart.py", line 11, in test_ten_percent_discount
    self.assertEqual(total([(20.00, 1), (5.00, 2)], discount_percent=10), 27.00)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -270.0 != 27.0

----------------------------------------------------------------------
Ran 3 tests in 0.002s

FAILED (failures=1)
```

A 10% discount on a 30.00 cart should give 27.00. The code subtracts ten times the subtotal.

## 4. Ask Claude to fix it

Start Claude Code in `~/first-task` and give it a context-full request, the kind the policy asks
for:

> `test_ten_percent_discount` in `test_cart.py` fails: `total()` in `cart.py` returns -270.0
> instead of 27.00 for a 10% discount on a 30.00 cart. Fix only `total()` so a
> `discount_percent` of 10 means ten percent. Do not change the tests. Verify with
> `python3 -m unittest`; expect `Ran 3 tests` and `OK`. Run it through the verifier before
> calling it done.

What to watch for:

- The change touches `cart.py` only.
- The `verifier` runs `python3 -m unittest` itself and ends its report with exactly one line,
  `GATE: PASS` or `GATE: FAIL`.
- On `GATE: FAIL` the failure goes back for another attempt, at most twice, and then to you.
- Claude reports the command it ran and its output, not just "fixed".

If the first attempt is wrong you will see the gate fail. That is the workflow working. Whether
the gate is used at all depends on the model following the policy; nothing forces it.

## 5. Check the evidence yourself

Do not take the report's word for it. Run the same command and read the diff:

```text
$ git diff
diff --git a/cart.py b/cart.py
index 844c56f..dc1c5bd 100644
--- a/cart.py
+++ b/cart.py
@@ -4,4 +4,4 @@
 def total(items, discount_percent=0):
     """Sum (price, quantity) pairs and apply a percentage discount, rounded to cents."""
     subtotal = sum(price * quantity for price, quantity in items)
-    return round(subtotal - subtotal * discount_percent, 2)
+    return round(subtotal - subtotal * discount_percent / 100, 2)

$ python3 -m unittest
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
```

That is the correct fix. A different correct fix is fine; a changed test is not.

## 6. Clean up

Delete the demo with `rm -rf ~/first-task`. To remove Stackwich itself, preview first:

```text
$ python3 ~/stackwich-tools/tools/uninstall.py ~/.claude
~/.claude/CLAUDE.md: would remove the Stackwich block; 4 other line(s) kept
~/.claude/agents/advisor.md: would remove (Stackwich agent)
~/.claude/agents/executor.md: would remove (Stackwich agent)
~/.claude/agents/verifier.md: would remove (Stackwich agent)
dry run: nothing changed; re-run with --apply to make these changes

$ python3 ~/stackwich-tools/tools/uninstall.py ~/.claude --apply
~/.claude/CLAUDE.md: removed the Stackwich block; 4 other line(s) kept
~/.claude/agents/advisor.md: removed (Stackwich agent)
~/.claude/agents/executor.md: removed (Stackwich agent)
~/.claude/agents/verifier.md: removed (Stackwich agent)
backup: ~/.claude/CLAUDE.md.stackwich-backup
```

It removes the policy block and only the agent files that carry the Stackwich author credit,
including renamed ones. Your own agents and the rest of `CLAUDE.md` stay. It refuses a block
with a missing marker instead of guessing. Then remove the plugin inside Claude Code:

```
/plugin uninstall stackwich
/plugin marketplace remove stackwich
```

`tools/test_tools.py` checks this walkthrough's demo in CI: the shipped `cart.py` must fail
exactly as shown, and the fix above must make it pass.
