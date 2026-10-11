"""第十五章：從程序外驗收第十四章的 TextMeter 命令契約。"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SAMPLE = 'AI 幫你工作。\n先檢查，再執行。\n\n保留成果。\n'.encode('utf-8')
EXPECTED = dict(bytes=61, lines=4, nonempty_lines=3, paragraphs=2, nonspace_characters=20)


class Blocked(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f'JSON 欄位重複：{key}')
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f'不接受非標準 JSON 數值：{value}')

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def check_stats(actual, expected):
    require(isinstance(actual, dict) and actual.keys() == expected.keys(), '統計欄位不符')
    require(all(type(value) is int for value in actual.values()), '統計值必須為整數，不接受布林或浮點數')
    require(actual == expected, f'統計結果不符，預期 {expected}，實際 {actual}')


def check_response(log, command, success):
    require(log['returncode'] is not None and log['returncode'] >= 0, '命令未正常結束')
    payload = strict_json(log['stdout'])
    require(isinstance(payload, dict), 'JSON 外層必須是物件')
    require(type(payload.get('schema_version')) is int and payload['schema_version'] == 1, '回應版本不符')
    require(type(payload.get('ok')) is bool and payload['ok'] is success, 'ok 與案例預期不符')
    require((log['returncode'] == 0) is success, '結束碼與案例預期不符')
    if success:
        require(payload.get('command') == command, 'command 不符')
        require('error' in payload and payload['error'] is None, '成功回應缺少 error=null')
        require(isinstance(payload.get('data'), dict), '成功回應缺少 data 物件')
    else:
        require('data' in payload and payload['data'] is None, '失敗回應缺少 data=null')
        error = payload.get('error')
        require(isinstance(error, dict) and all(isinstance(error.get(key), str) and error[key].strip()
                                               for key in ['code', 'message']), '缺少可判讀的錯誤')
    return payload['data']


def invoke(executable, args, cwd, log_path, timeout):
    log = {'args': [executable, *args], 'cwd': str(cwd), 'returncode': None,
           'stdout': '', 'stderr': ''}
    problem = None
    try:
        completed = subprocess.run(log['args'], cwd=cwd, stdin=subprocess.DEVNULL,
                                   capture_output=True, timeout=timeout)
        log.update(returncode=completed.returncode,
                   stdout=completed.stdout.decode('utf-8', errors='replace'),
                   stderr=completed.stderr.decode('utf-8', errors='replace'))
        # 保存可讀日誌，但不讓替換過的非法 UTF-8 被當成有效回應。
        completed.stdout.decode('utf-8')
    except UnicodeError:
        log['stdout_bytes_hex'] = completed.stdout.hex()
        problem = ValueError('stdout 不是有效 UTF-8')
    except subprocess.TimeoutExpired as error:
        log.update(stdout=(error.stdout or b'').decode('utf-8', errors='replace'),
                   stderr=(error.stderr or b'').decode('utf-8', errors='replace'))
        problem = Blocked('命令逾時；未完成驗收')
    except OSError as error:
        problem = Blocked(f'無法啟動命令：{error}')
    if problem:
        log['execution_error'] = str(problem)
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    if problem:
        raise problem
    return log


def cases():
    yield 'sample', SAMPLE, EXPECTED, 'analyze'
    yield 'empty', b'', dict.fromkeys(EXPECTED, 0), 'analyze'
    for name, content in [('crlf', b'A\r\nB\r\n\r\nC\r\n'), ('cr', b'A\rB\r\rC\r')]:
        yield name, content, dict(bytes=len(content), lines=4, nonempty_lines=3, paragraphs=2, nonspace_characters=3), 'analyze'
    yield 'bom', b'\xef\xbb\xbfA\n', dict(bytes=5, lines=1, nonempty_lines=1, paragraphs=1, nonspace_characters=1), 'analyze'
    for name, content in [('invalid-utf8', b'\xff'), ('nul', b'A\x00B'),
                          ('oversize', b'A' * (1048576 + 1)), ('missing', None), ('directory', None)]:
        yield name, content, None, 'analyze'
    yield 'missing-argument', None, None, 'argument'
    for mode in ['export', 'repeat-export', 'source-output', 'symlink-output', 'missing-parent']:
        yield mode, SAMPLE, EXPECTED, mode


def run_case(executable, folder, cwd, name, content, expected, mode, timeout):
    folder.mkdir()
    source = folder / '中文 範例.txt'
    if content is not None:
        source.write_bytes(content)
    if name == 'directory':
        source.mkdir()
    row = {'name': name, 'status': 'passed', 'detail': '命令契約符合本案例', 'logs': []}
    step = 0

    def call(command, arguments, success):
        nonlocal step
        step += 1
        log_path = folder / f'command-{step}.json'
        row['logs'].append(str(log_path))
        log = invoke(executable, ['--json', command, *arguments], cwd, log_path, timeout)
        return check_response(log, command, success)

    protected = {}
    if content is not None:
        protected[source] = content
    link_target = None
    destination = folder / 'report.json'
    try:
        if mode == 'analyze':
            data = call('analyze', [str(source)], expected is not None)
            if expected is not None:
                check_stats(data, expected)
        elif mode == 'argument':
            call('analyze', [], False)
        else:
            if mode == 'source-output':
                destination = source
            elif mode == 'missing-parent':
                destination = folder / 'not-created' / 'report.json'
            elif mode == 'symlink-output':
                target = folder / 'keep.json'
                target.write_bytes(b'keep this report\n')
                protected[target] = target.read_bytes()
                try:
                    destination.symlink_to(target.name)
                except OSError as error:
                    raise Blocked(f'環境無法建立符號連結：{error}') from error
                link_target = target.name
            success = mode in {'export', 'repeat-export'}
            data = call('export', [str(source), '--output', str(destination)], success)
            if success:
                check_stats(data.get('stats'), expected)
                require(isinstance(data.get('output'), str), '匯出回應缺少 output 字串')
                reported = Path(data['output'])
                if not reported.is_absolute():
                    reported = cwd / reported
                require(reported.resolve() == destination.resolve(), '回應的輸出位置不符')
                require(destination.is_file() and not destination.is_symlink(), '匯出檔案不存在或是符號連結')
                check_stats(strict_json(destination.read_text(encoding='utf-8')), expected)
                if mode == 'repeat-export':
                    protected[destination] = destination.read_bytes()
                    call('export', [str(source), '--output', str(destination)], False)
            elif mode == 'missing-parent':
                require(not destination.parent.exists(), '失敗操作意外建立輸出父目錄')
    except Blocked as error:
        row.update(status='blocked', detail=str(error))
    except (OSError, ValueError) as error:
        row.update(status='failed', detail=str(error))
    finally:
        changes = []
        for path, before in protected.items():
            try:
                unchanged = not path.is_symlink() and path.read_bytes() == before
            except OSError:
                unchanged = False
            if not unchanged:
                changes.append(path.name)
        if link_target is not None and (not destination.is_symlink() or str(destination.readlink()) != link_target):
            changes.append('report.json 符號連結')
        if name == 'missing' and (source.exists() or source.is_symlink()):
            changes.append('原本不存在的輸入')
        if name == 'directory' and (source.is_symlink() or not source.is_dir() or any(source.iterdir())):
            changes.append('輸入目錄')
        row['protected_files_unchanged'] = not changes
        if changes:
            row.update(status='failed', detail=row['detail'] + '；受保護檔案改變：' + '、'.join(changes))
    return row


def run_suite(executable, output, timeout=10):
    # 新目錄失敗即拒絕，不覆寫前輪報告。
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    with tempfile.TemporaryDirectory(prefix='textmeter-cwd-') as temporary:
        cwd = Path(temporary)
        for name, content, expected, mode in cases():
            rows.append(run_case(executable, output / name, cwd, name, content, expected, mode, timeout))
    counts = {status: sum(row['status'] == status for row in rows) for status in ['passed', 'failed', 'blocked']}
    status = 'failed' if counts['failed'] else 'incomplete' if counts['blocked'] else 'passed_contract_checks'
    report = {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
              'executable': executable, 'status': status, 'counts': counts, 'cases': rows,
              'scope': 'TextMeter 命令契約；不等於完整 harness、原始碼審查或安全驗證'}
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# TextMeter 命令驗收報告', '', f'結果：`{status}`', '',
             '| 案例 | 狀態 | 說明 |', '| --- | --- | --- |']
    for row in rows:
        detail = row['detail'].replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {row['name']} | {row['status']} | {detail} |")
    lines += ['', report['scope'], '']
    (output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    return report, 1 if counts['failed'] else 2 if counts['blocked'] else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', required=True, help='命令名稱或可執行檔路徑，不含附加參數')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--timeout', type=int, default=10, help='每次命令逾時秒數，1～60')
    args = parser.parse_args(argv)
    try:
        require(1 <= args.timeout <= 60, 'timeout 必須介於 1～60 秒')
        found = shutil.which(args.cli)
        require(found is not None, f'找不到可執行命令：{args.cli}')
        # 不 resolve 符號連結，以保留可執行入口的路徑語意。
        report, code = run_suite(str(Path(found).absolute()), args.output, args.timeout)
        print(json.dumps({'status': report['status'], 'counts': report['counts'],
                          'report': str(args.output.absolute() / 'report.json')}, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError) as error:
        print(f'無法完成驗收：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
