"""第九章：保存教材工作狀態，保留每次嘗試，明確要求重試。

限 Linux／WSL 的單機教學流程；不是背景佇列或自動續跑服務。
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

MAX_ATTEMPTS = 3
ACTIVE = {'created', 'checking', 'planning', 'building'}
FILES = ['slides.odp', 'slides.pptx', 'slides.pdf', 'handout.odt', 'handout.pdf']


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    """在同一目錄寫完整暫存檔，再替換；不宣稱斷電後的完整交易保證。"""
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            name = stream.name
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(folder):
    with (folder / '.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('此工作正由另一個執行程序使用') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def read_state(folder):
    state = json.loads((folder / 'state.json').read_text(encoding='utf-8'))
    if (not isinstance(state, dict) or type(state.get('schema_version')) is not int
            or state['schema_version'] != 1 or state.get('status') not in ACTIVE | {'failed', 'needs_review'}
            or not isinstance(state.get('attempts'), list)
            or not isinstance(state.get('input_sha256'), str) or not isinstance(state.get('workspace'), str)):
        raise ValueError('不支援或損壞的 state.json；請保留原始紀錄再調查')
    return state


def validate_response(completed, command):
    try:
        result = json.loads(completed.stdout)
    except (ValueError, TypeError) as error:
        raise ValueError('stdout 不是單一有效 JSON') from error
    if (not isinstance(result, dict) or type(result.get('schema_version')) is not int
            or result['schema_version'] != 1 or result.get('command') != command
            or type(result.get('ok')) is not bool):
        raise ValueError('回應版本、命令名稱或 ok 型別不符')
    if result['ok']:
        if completed.returncode != 0 or not isinstance(result.get('data'), dict) or result.get('error') is not None:
            raise ValueError('成功回應與結束碼或欄位不一致')
    else:
        error = result.get('error')
        if (completed.returncode == 0 or not isinstance(error, dict)
                or not isinstance(error.get('code'), str) or not isinstance(error.get('message'), str)):
            raise ValueError('失敗回應與結束碼或 error 欄位不一致')
    return result


def retry_advice(code):
    if code in {'invalid_input', 'invalid_arguments', 'input_changed'}:
        return '修正來源後建立新工作；不要修改既有工作的 input.json'
    if code == 'missing_dependency':
        return '修復依賴後，可手動 retry；本程式不會自動安裝工具'
    return '先查看本次命令紀錄及部分成果，排除原因後再決定是否手動 retry'


def run_attempt(folder, state):
    if digest((folder / 'input.json').read_bytes()) != state['input_sha256']:
        raise ValueError('工作輸入快照已改變，拒絕執行；請建立新工作')
    number = len(state['attempts']) + 1
    if number > MAX_ATTEMPTS:
        raise ValueError('已達最多 3 次嘗試（含第一次），請先調查原因')
    attempt_dir = folder / f'attempt-{number:03d}'
    attempt_dir.mkdir()
    output = attempt_dir / 'artifacts'
    attempt = {'number': number, 'started_at': now(), 'status': 'running', 'steps': [], 'output': str(output)}
    state['attempts'].append(attempt)

    def save():
        state['updated_at'] = now()
        write_json(folder / 'state.json', state)

    def fail(code, message):
        state.update(status='failed', error={'code': code, 'message': message}, retry_advice=retry_advice(code))
        attempt.update(status='failed', finished_at=now(), error=state['error'])
        save()
        return 1

    for command, status in [('doctor', 'checking'), ('check', 'checking'), ('plan', 'planning'), ('build', 'building')]:
        state.update(status=status, current_step=command, error=None, retry_advice=None)
        save()
        args = [sys.executable, '-m', 'lesson_kit', '--workspace', state['workspace'], '--json', command]
        if command != 'doctor':
            args.append(str(folder / 'input.json'))
        if command in {'plan', 'build'}:
            args += ['--output', str(output)]
        log_path = attempt_dir / f'{command}.json'
        try:
            completed = subprocess.run(args, capture_output=True, text=True)
            write_json(log_path, {'args': args, 'returncode': completed.returncode,
                                  'stdout': completed.stdout, 'stderr': completed.stderr})
            attempt['steps'].append({'command': command, 'log': str(log_path), 'returncode': completed.returncode})
            try:
                payload = validate_response(completed, command)
            except ValueError as error:
                return fail('protocol_error', str(error))
            if not payload['ok']:
                return fail(payload['error']['code'], payload['error']['message'])
            if command == 'build':
                data = payload['data']
                report = json.loads((output / 'verification.json').read_text(encoding='utf-8'))
                if (data.get('status') != 'passed_basic_checks' or data.get('needs_visual_review') is not True
                        or not isinstance(report, dict) or report.get('status') != 'passed_basic_checks'
                        or report.get('source_sha256') != state['input_sha256'] or report.get('source_unchanged') is not True
                        or report.get('pptx_slide_text_verified') is not True
                        or any(not (output / name).is_file() for name in FILES)):
                    return fail('invalid_result', '建置結果與驗證紀錄或預期成品不符')
                attempt['artifact_sha256'] = {name: digest((output / name).read_bytes()) for name in FILES}
            save()
        except (OSError, ValueError) as error:
            return fail('execution_error', str(error))
    if digest((folder / 'input.json').read_bytes()) != state['input_sha256']:
        return fail('input_changed', '工作輸入快照在執行期間改變')
    state.update(status='needs_review', current_step=None, error=None, retry_advice=None)
    attempt.update(status='needs_review', finished_at=now())
    save()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start', help='建立新工作並執行一次')
    start.add_argument('--input', type=Path, required=True)
    start.add_argument('--workspace', type=Path, default=Path.cwd())
    for child in [start, commands.add_parser('status', help='讀取最後保存的狀態'), commands.add_parser('retry', help='失敗後明確重試一次')]:
        child.add_argument('--job-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        folder = args.job_dir.resolve()
        if args.command == 'start':
            if args.job_dir.is_symlink():
                raise ValueError('工作目錄不可為符號連結')
            content = args.input.read_bytes()
            folder.mkdir(parents=True, exist_ok=False)
            with locked(folder):
                (folder / 'input.json').write_bytes(content)
                state = {'schema_version': 1, 'job_id': str(uuid.uuid4()), 'status': 'created',
                         'created_at': now(), 'workspace': str(args.workspace.resolve()),
                         'source_path': str(args.input.resolve()), 'input_sha256': digest(content), 'attempts': []}
                write_json(folder / 'state.json', state)
                code = run_attempt(folder, state)
        elif args.command == 'status':
            state, code = read_state(folder), 0
        else:
            with locked(folder):
                state = read_state(folder)
                if state['status'] != 'failed':
                    raise ValueError('只允許重試 failed；執行中或意外中斷的工作須先人工調查，已產生的成果不重建')
                if state.get('error', {}).get('code') in {'invalid_input', 'invalid_arguments', 'input_changed'}:
                    raise ValueError('請修正來源後建立新工作；既有輸入快照保持不變')
                code = run_attempt(folder, state)
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
