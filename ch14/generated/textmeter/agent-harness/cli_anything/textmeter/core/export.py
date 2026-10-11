"""Create a report without replacing existing files or symlinks."""
import json
from pathlib import Path
from cli_anything.textmeter.utils.textmeter_backend import analyze


def export_report(source: str | Path, output: str | Path) -> dict:
    """Analyze first, then exclusively create a UTF-8 JSON report."""
    stats = analyze(source)
    payload = json.dumps(stats, ensure_ascii=False, indent=2) + "\n"
    target = Path(output)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(payload)
    return {"output": str(target.absolute()), "stats": stats}
