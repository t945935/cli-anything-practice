"""純文字統計後端；沒有 CLI，也不修改輸入。"""
from pathlib import Path

MAX_BYTES = 1024 * 1024


def analyze_file(path: str | Path) -> dict[str, int]:
    """讀取至多 1 MiB 的 UTF-8 一般檔案，允許 UTF-8 BOM。"""
    source = Path(path)
    if not source.is_file():
        raise ValueError('輸入必須是存在的一般檔案')
    with source.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('檔案超過 1 MiB 上限')
    text = raw.decode('utf-8-sig')
    if '\x00' in text:
        raise ValueError('不接受含 NUL 的文字')
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = normalized.split('\n') if normalized else []
    if lines and lines[-1] == '':
        lines.pop()
    paragraphs = 0
    inside = False
    for line in lines:
        nonempty = bool(line.strip())
        if nonempty and not inside:
            paragraphs += 1
        inside = nonempty
    return {
        'bytes': len(raw),
        'lines': len(lines),
        'nonempty_lines': sum(bool(line.strip()) for line in lines),
        'paragraphs': paragraphs,
        'nonspace_characters': sum(not character.isspace() for character in text),
    }
