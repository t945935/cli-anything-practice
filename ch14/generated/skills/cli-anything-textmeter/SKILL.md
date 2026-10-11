---
name: cli-anything-textmeter
description: Analyze UTF-8 text files or export TextMeter statistics using the installed cli-anything-textmeter command. Use for this book's TextMeter CLI, not general document editing.
---

# TextMeter CLI

Use the installed command. It delegates to the required TextMeter backend; it does not count linguistic words. Input must be a general UTF-8 file of at most 1 MiB, with optional BOM and no NUL. Paths may contain spaces and Chinese characters; pass them as one argument.

From the reader repository root, install in a dedicated environment if installation is part of the user's request:

```bash
python -m pip install ./ch14/textmeter
python -m pip install ./ch14/generated/textmeter/agent-harness
```

The book package has not been published to PyPI. Do not substitute a package with a similar name from an index.

```bash
cli-anything-textmeter --json analyze "input.txt"
cli-anything-textmeter --json export "input.txt" --output "report.json"
```

The output parent directory must exist. Export exclusively creates the report and refuses existing files and symlinks. Keep input intact. On a write interruption, inspect any partial new report before choosing a fresh destination.

For one-shot commands, parse the single stdout JSON object. Success has integer schema_version=1, ok=true, data, error=null, exit 0. Handled errors have ok=false, data=null and error.code/message, exit 2. Check both the response and exit code. For analyze, data holds five integer counters; for export, data holds output and stats. Read back an exported file before declaring it verified.

No subcommand starts REPL. Use help, analyze, export, quit or exit. REPL errors do not end the loop. There is no project command, undo/redo or persisted session. Use one-shot commands for automation; --json alone and --json repl are rejected. --help is ordinary text.

To validate a candidate, use ch15/check_cli.py with a new output directory, then check the report. Sixteen contract cases do not cover all inputs or constitute a security sandbox.
