"""Verify delegation and real report protection."""
import json
from unittest.mock import patch
import pytest
from cli_anything.textmeter.utils.textmeter_backend import analyze
from cli_anything.textmeter.core.export import export_report


def test_delegates_to_installed_backend(tmp_path):
    path = tmp_path / "input.txt"
    with patch("textmeter.analyze_file", return_value={"sentinel": 7}) as call:
        assert analyze(path) == {"sentinel": 7}
        call.assert_called_once_with(path)


def test_real_statistics(tmp_path):
    path = tmp_path / "中文 空白.txt"
    path.write_bytes("A\r\n\r\n中\r\n".encode())
    assert analyze(path) == dict(bytes=10, lines=3, nonempty_lines=2,
                                paragraphs=2, nonspace_characters=2)


def test_export_real_content(tmp_path):
    source, target = tmp_path / "input.txt", tmp_path / "result.json"
    source.write_bytes(b"A\n")
    result = export_report(source, target)
    assert result["stats"] == json.loads(target.read_text())
    assert result["stats"]["bytes"] == 2
    assert source.read_bytes() == b"A\n"


def test_source_equal_output(tmp_path):
    source = tmp_path / "input.txt"
    source.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        export_report(source, source)
    assert source.read_bytes() == b"original"


@pytest.mark.parametrize("symlink", [False, True])
def test_preserves_existing_target(tmp_path, symlink):
    source, target = tmp_path / "input.txt", tmp_path / "result.json"
    source.write_bytes(b"original")
    if symlink:
        target.symlink_to(source)
    else:
        target.write_bytes(b"keep")
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        export_report(source, target)
    assert target.read_bytes() == before
