"""lesson-kit：統一教材檢查、計畫、建置與環境診斷的命令介面。"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

TOOLS = ['cli-anything-libreoffice', 'libreoffice', 'pdfinfo', 'pdftotext', 'pdftoppm']
OUTPUTS = ['slides.odp', 'slides.pptx', 'slides.pdf', 'handout.odt', 'handout.pdf']


class Failure(Exception):
    def __init__(self, message, kind='invalid_input', exit_code=2, data=None):
        super().__init__(message)
        self.kind, self.exit_code, self.data = kind, exit_code, data


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Failure(message, 'invalid_arguments')


def parser():
    p = Parser(description='將課程 JSON 轉成可驗證的簡報與講義。')
    p.add_argument('--json', action='store_true', help='stdout 輸出單一 JSON 結果（help 除外）')
    p.add_argument('--workspace', type=Path, default=Path.cwd(), help='完整讀者儲存庫根目錄；預設目前目錄')
    commands = p.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor', help='檢查後端、素材與工具路徑；不測試轉檔')
    for name, help_text in [('check', '檢查課程資料'), ('plan', '預覽輸出計畫，不產生教材'), ('build', '產生並驗證教材')]:
        child = commands.add_parser(name, help=help_text)
        child.add_argument('input', type=Path, help='課程 JSON 路徑')
        if name != 'check':
            child.add_argument('--output', required=True, type=Path, help='尚未存在的輸出資料夾')
    return p


def inspect_environment(workspace):
    files = ['ch07/build_lesson.py', 'reference/web.jpg', 'reference/square.png', 'reference/padded.png']
    return {'workspace': str(workspace),
            'files': {name: (workspace / name).is_file() for name in files},
            'tools': {name: shutil.which(name) for name in TOOLS},
            'scope': '僅檢查檔案與 PATH；版本、轉檔與版面尚未驗證'}


def require_environment(workspace):
    result = inspect_environment(workspace)
    if not all(result['files'].values()) or not all(result['tools'].values()):
        raise Failure('缺少建置所需的檔案或工具，請查看診斷結果', 'missing_dependency', 3, result)
    return result


def load_backend(workspace):
    script = workspace / 'ch07/build_lesson.py'
    if not script.is_file():
        raise Failure('找不到 ch07/build_lesson.py；請用 --workspace 指定完整讀者儲存庫', 'missing_dependency', 3)
    spec = importlib.util.spec_from_file_location('lesson_kit_ch07_backend', script)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def execute(args):
    workspace = args.workspace.resolve()
    if args.command == 'doctor':
        return require_environment(workspace)
    backend = load_backend(workspace)
    source = args.input.resolve()
    try:
        lesson = backend.load_lesson(source)
    except (OSError, ValueError) as error:
        raise Failure(str(error)) from error
    result = {'title': lesson['title'], 'slides': len(lesson['slides']), 'input': str(source)}
    if args.command == 'check':
        return result
    # 先檢查原始路徑的符號連結，避免 resolve 隱藏尚未有目標的連結。
    if args.output.is_symlink() or args.output.exists():
        raise Failure('輸出路徑已存在，請換新名稱', 'output_exists')
    output = args.output.resolve()
    for parent in output.parents:
        if parent.exists() and not parent.is_dir():
            raise Failure('輸出路徑的上層不是資料夾', 'invalid_output')
    result.update(output=str(output), outputs=OUTPUTS + ['assets/', 'previews/', 'verification.json'], images_embedded=False)
    if args.command == 'plan':
        return result
    require_environment(workspace)
    command = [sys.executable, str(workspace / 'ch07/build_lesson.py'), '--input', str(source), '--output', str(output)]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        raise Failure('第七章建置流程失敗；請查看錯誤與已產生的驗證紀錄', 'build_failed', 1,
                      {'backend_exit_code': completed.returncode, 'output': str(output),
                       'stdout': completed.stdout, 'stderr': completed.stderr})
    try:
        report = json.loads((output / 'verification.json').read_text(encoding='utf-8'))
        valid = (isinstance(report, dict) and report.get('status') == 'passed_basic_checks'
                 and report.get('source_unchanged') is True and report.get('pptx_slide_text_verified') is True
                 and report.get('slide_pages') == len(lesson['slides'])
                 and all((output / name).is_file() for name in OUTPUTS))
    except (OSError, ValueError):
        valid = False
    if not valid:
        raise Failure('後端回傳成功，但成品或驗證紀錄不完整', 'invalid_result', 1, {'output': str(output)})
    result.update(status=report['status'], slide_pages=report['slide_pages'], handout_pages=report.get('handout_pages'),
                  needs_visual_review=True, verification=str(output / 'verification.json'))
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    json_mode = '--json' in argv
    command, data, error, code = None, None, None, 0
    try:
        args = parser().parse_args(argv)
        command, json_mode = args.command, args.json
        data = execute(args)
    except Failure as failure:
        code, data = failure.exit_code, failure.data
        error = {'code': failure.kind, 'message': str(failure)}
    except Exception as failure:
        code = 1
        error = {'code': 'execution_error', 'message': str(failure)}
    payload = {'schema_version': 1, 'command': command, 'ok': code == 0, 'data': data, 'error': error}
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif code:
        print(f"失敗 [{error['code']}]：{error['message']}", file=sys.stderr)
        if data is not None:
            print(json.dumps(data, ensure_ascii=False, indent=2), file=sys.stderr)
    else:
        print(f'{command} 完成')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return code
