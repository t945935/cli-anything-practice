"""整理本書 TextMeter 0.1.0 參考工具的交接資料，不建立或發布 wheel。"""
import argparse
from datetime import datetime, timezone
from email.parser import Parser
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    'cli-anything-practice-textmeter-core': ('textmeter.py', 'ch14/textmeter/textmeter.py', []),
    'cli-anything-practice-textmeter-reference': (
        'textmeter_reference.py', 'ch15/reference_adapter/textmeter_reference.py',
        ['cli-anything-practice-textmeter-core==0.1.0']),
}
SOURCES = {
    'source/textmeter/textmeter.py': 'ch14/textmeter/textmeter.py',
    'source/textmeter/pyproject.toml': 'ch14/textmeter/pyproject.toml',
    'source/textmeter/README.md': 'ch14/textmeter/README.md',
    'source/textmeter/samples/中文 範例.txt': 'ch14/textmeter/samples/中文 範例.txt',
    'source/textmeter/samples/expected.json': 'ch14/textmeter/samples/expected.json',
    'source/reference_adapter/textmeter_reference.py': 'ch15/reference_adapter/textmeter_reference.py',
    'source/reference_adapter/pyproject.toml': 'ch15/reference_adapter/pyproject.toml',
    'check_cli.py': 'ch15/check_cli.py',
    'INSTALL.md': 'ch16/INSTALL.md',
}


def sha(content):
    return hashlib.sha256(content).hexdigest()


def validate_wheel(content, package, root):
    import io
    module, source, dependencies = PACKAGES[package]
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError('wheel ZIP 項目重複或 CRC 錯誤')
        metadata_files = [name for name in names if name.endswith('.dist-info/METADATA')]
        if len(metadata_files) != 1:
            raise ValueError('wheel 必須恰有一份套件 METADATA')
        metadata = Parser().parsestr(archive.read(metadata_files[0]).decode('utf-8'))
        if metadata.get_all('Name') != [package] or metadata.get_all('Version') != ['0.1.0']:
            raise ValueError('wheel 名稱或版本不符合本章指定套件')
        requires = [value.replace(' ', '') for value in metadata.get_all('Requires-Dist', [])]
        if sorted(requires) != sorted(dependencies):
            raise ValueError('wheel 執行期相依與本章範圍不符')
        if archive.read(module) != (root / source).read_bytes():
            raise ValueError(f'wheel 中的 {module} 與目前來源不同，請重新封裝')


def make_bundle(wheels, output, root=ROOT):
    if output.exists() or output.is_symlink():
        raise ValueError('交接目錄已存在，請使用新路徑')
    prepared = {}
    requirements = []
    for package in PACKAGES:
        filename = package.replace('-', '_') + '-0.1.0-py3-none-any.whl'
        content = (wheels / filename).read_bytes()
        validate_wheel(content, package, root)
        prepared['wheels/' + filename] = content
        requirements.append(f'{package}==0.1.0 --hash=sha256:{sha(content)}')
    for destination, source in SOURCES.items():
        prepared[destination] = (root / source).read_bytes()
    prepared['requirements.txt'] = ('\n'.join(requirements) + '\n').encode('utf-8')
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, timeout=10)
        commit = result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        commit = None
    release = {
        'schema_version': 1,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'kind': 'book_reference_textmeter_bundle',
        'source_repository': 'https://github.com/t945935/cli-anything-practice',
        'repository_head': commit,
        'python_used_to_assemble': sys.version.split()[0],
        'packages': {name: '0.1.0' for name in PACKAGES},
        'source_sha256': {destination: sha(prepared[destination]) for destination in SOURCES},
        'notes': '來源為整理時的工作目錄副本，HEAD 不保證工作目錄未修改；雜湊不是作者簽章或可重現建置證明。',
    }
    prepared['release.json'] = (json.dumps(release, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    checksums = '\n'.join(f'{sha(content)}  {name}' for name, content in sorted(prepared.items())) + '\n'
    prepared['SHA256SUMS'] = checksums.encode('utf-8')
    output.mkdir(parents=True, exist_ok=False)
    for name, content in prepared.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return release


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheels', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        make_bundle(args.wheels, args.output)
        print(f'交接資料已建立：{args.output}；請在新環境安裝與驗收。')
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f'無法建立交接資料：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
