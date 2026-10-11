"""第十二章：盤點本機工具箱並比較兩次紀錄；不安裝、升級或發布。"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
import platform
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ['cli-anything-hub', 'cli-anything-libreoffice', 'cli-anything-gimp',
            'cli-anything-practice-lesson-kit', 'pillow', 'defusedxml']
PROBES = {'cli-hub': ['--help'], 'cli-anything-libreoffice': ['--help'],
          'cli-anything-gimp': ['--help'], 'lesson-kit': ['--help'],
          'libreoffice': ['--version'], 'pdfinfo': ['-v'], 'pdftotext': ['-v'], 'pdftoppm': ['-v']}


def normalize(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def installed_packages():
    result = {}
    for distribution in metadata.distributions():
        name = distribution.metadata.get('Name')
        if not name:
            continue
        item = {'version': distribution.version}
        direct = distribution.read_text('direct_url.json')
        if direct:
            data = json.loads(direct)
            # 僅記錄追查版本需要的欄位，不保存可能含憑證的 URL。
            item['source'] = {'vcs': data.get('vcs_info', {}).get('vcs'),
                              'commit_id': data.get('vcs_info', {}).get('commit_id'),
                              'editable': data.get('dir_info', {}).get('editable', False)}
        result[normalize(name)] = item
    return dict(sorted(result.items()))


def probe(args, timeout=30):
    try:
        completed = subprocess.run(list(map(str, args)), capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return {'returncode': completed.returncode, 'stdout': completed.stdout, 'stderr': completed.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'returncode': None, 'stdout': '', 'stderr': str(error)}


def tracked_manifest(root, names):
    result = {}
    for name in filter(None, names.split('\0')):
        path = root / name
        # 符號連結記錄其目標字串，不追蹤連結到儲存庫之外的檔案。
        if path.is_symlink():
            content = str(path.readlink()).encode('utf-8')
        else:
            content = path.read_bytes()
        result[name] = hashlib.sha256(content).hexdigest()
    return dict(sorted(result.items()))


def capture(run_tests=False):
    report = {'schema_version': 1, 'kind': 'toolbox_snapshot',
              'captured_at': datetime.now(timezone.utc).isoformat(),
              'runtime': {'python': platform.python_version(), 'implementation': platform.python_implementation(),
                          'executable': sys.executable, 'system': platform.system(),
                          'release': platform.release(), 'machine': platform.machine()},
              'packages': installed_packages(), 'tools': {}, 'repository': {}, 'checks': {}, 'issues': []}
    for name in REQUIRED:
        if name not in report['packages']:
            report['issues'].append('缺少本書套件：' + name)
    for name, args in PROBES.items():
        path = shutil.which(name)
        item = {'path': path, 'file_sha256': None}
        if path:
            try:
                item['file_sha256'] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            except OSError as error:
                report['issues'].append(f'{name} 入口檔案無法讀取：{error}')
            item.update(probe([path, *args]))
        else:
            item.update(returncode=None, stdout='', stderr='PATH 中找不到命令')
        # 原始 stderr 可能含 PID／時間戳；保留原文，但以識別行做環境比較。
        identifying_output = item['stdout'].strip() or item['stderr'].strip()
        item['identifier'] = identifying_output.splitlines()[0] if item['returncode'] == 0 and identifying_output else None
        report['tools'][name] = item
        if item['returncode'] != 0:
            report['issues'].append('工具入口或版本查詢失敗：' + name)
    git_head = probe(['git', 'rev-parse', 'HEAD'])
    git_status = probe(['git', 'status', '--porcelain'])
    git_files = probe(['git', 'ls-files', '-z'])
    report['repository'] = {'head': git_head['stdout'].strip() if git_head['returncode'] == 0 else None,
                            'working_tree_status': git_status['stdout'], 'files': {}}
    if any(item['returncode'] != 0 for item in [git_head, git_status, git_files]):
        report['issues'].append('無法完整讀取 Git 紀錄；請使用完整 Git clone')
    else:
        try:
            report['repository']['files'] = tracked_manifest(ROOT, git_files['stdout'])
        except OSError as error:
            report['issues'].append('已追蹤檔案無法讀取：' + str(error))
    report['checks']['pip_check'] = probe([sys.executable, '-m', 'pip', 'check'])
    if report['checks']['pip_check']['returncode'] != 0:
        report['issues'].append('pip check 未通過或無法執行')
    if run_tests:
        report['checks']['tests'] = probe([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], timeout=180)
        if report['checks']['tests']['returncode'] != 0:
            report['issues'].append('基本測試未通過或無法完成')
    else:
        report['checks']['tests'] = {'status': 'not_run'}
    report['status'] = 'attention_required' if report['issues'] else 'recorded'
    return report


def comparison_view(snapshot):
    if (not isinstance(snapshot, dict) or type(snapshot.get('schema_version')) is not int
            or snapshot['schema_version'] != 1 or snapshot.get('kind') != 'toolbox_snapshot'):
        raise ValueError('只接受 schema_version 1 的 toolbox_snapshot')
    for key in ['runtime', 'packages', 'tools', 'repository', 'checks']:
        if not isinstance(snapshot.get(key), dict):
            raise ValueError('紀錄缺少物件欄位：' + key)
    view = {key: snapshot[key] for key in ['runtime', 'packages', 'repository']}
    view['tools'] = {name: {key: item.get(key) for key in ['path', 'file_sha256', 'returncode', 'identifier']}
                     for name, item in snapshot['tools'].items()}
    return view


def differences(before, after, prefix=''):
    changes = []
    for key in sorted(before.keys() | after.keys()):
        name = prefix + key
        if key not in before:
            changes.append({'field': name, 'change': 'added', 'after': after[key]})
        elif key not in after:
            changes.append({'field': name, 'change': 'removed', 'before': before[key]})
        elif isinstance(before[key], dict) and isinstance(after[key], dict):
            changes += differences(before[key], after[key], name + '.')
        elif before[key] != after[key]:
            changes.append({'field': name, 'change': 'changed', 'before': before[key], 'after': after[key]})
    return changes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    snapshot = commands.add_parser('snapshot', help='記錄版本、命令入口、Git 與 pip check')
    snapshot.add_argument('--run-tests', action='store_true')
    compare = commands.add_parser('compare', help='比較兩份紀錄；不判定功能相容性')
    compare.add_argument('--before', type=Path, required=True)
    compare.add_argument('--after', type=Path, required=True)
    for child in [snapshot, compare]:
        child.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('輸出目錄已存在，請使用新名稱')
        if args.command == 'snapshot':
            report = capture(args.run_tests)
            filename = 'snapshot.json'
            code = 1 if report['issues'] else 0
            lines = ['# 工具箱盤點', '', f"紀錄狀態：`{report['status']}`。", '',
                     '此紀錄不等於文件轉檔、教材內容或版面驗證通過。', '', '## 必要套件', '',
                     '| 套件 | 版本 |', '| --- | --- |']
            lines += [f"| {name} | {report['packages'].get(name, {}).get('version', '缺少')} |" for name in REQUIRED]
            lines += ['', '## 待處理項目', '', *['- ' + item for item in report['issues']]]
            if not report['issues']:
                lines.append('未發現本次盤點涵蓋的依賴或入口問題。')
            lines += ['', '基本測試：' + ('已執行，詳見 snapshot.json。' if args.run_tests else '未執行。'), '']
        else:
            before = json.loads(args.before.read_text(encoding='utf-8'))
            after = json.loads(args.after.read_text(encoding='utf-8'))
            changes = differences(comparison_view(before), comparison_view(after))
            report = {'schema_version': 1, 'kind': 'toolbox_comparison', 'status': 'changed' if changes else 'unchanged',
                      'functional_compatibility': 'not_evaluated', 'changes': changes,
                      'before_evidence': {'status': before.get('status'), 'issues': before.get('issues'), 'checks': before['checks']},
                      'after_evidence': {'status': after.get('status'), 'issues': after.get('issues'), 'checks': after['checks']}}
            filename = 'comparison.json'
            code = 3 if changes else 0
            lines = ['# 工具箱差異', '', f"結果：`{report['status']}`，共 {len(changes)} 項差異。", '',
                     '功能相容性尚未判定；兩次 pip check 與測試結果另存於 JSON 的 evidence 欄位。', '']
            lines += ['- ' + item['field'] + '：' + item['change'] for item in changes]
        args.output.mkdir(parents=True)
        (args.output / filename).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        (args.output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
        print(json.dumps({'status': report['status'], 'report': str((args.output / filename).resolve())}, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    sys.exit(main())
