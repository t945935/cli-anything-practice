"""Call the installed original backend without copying its algorithm."""
from pathlib import Path
import textmeter


def analyze(path: str | Path) -> dict[str, int]:
    """Read a real file through the required TextMeter backend."""
    return textmeter.analyze_file(path)
