"""手寫驗收參考介面；不實作完整 CLI-Anything harness。"""
import argparse
import json
import os
from pathlib import Path
import sys

from textmeter import analyze_file


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = Parser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    commands = parser.add_subparsers(dest='command', required=True, parser_class=Parser)
    commands.add_parser('analyze').add_argument('input', type=Path)
    export = commands.add_parser('export')
    export.add_argument('input', type=Path)
    export.add_argument('--output', type=Path, required=True)
    command = None
    fault = os.environ.get('TEXTMETER_DEMO_FAULT', '')
    try:
        args = parser.parse_args(argv)
        command = args.command
        stats = analyze_file(args.input)
        if fault == 'boolean-count':
            stats['lines'] = True
        data = stats
        if command == 'export':
            # 故障模式刻意覆寫；只供本章建立的測試資料使用。
            mode = 'w' if fault == 'overwrite' else 'x'
            with args.output.open(mode, encoding='utf-8') as stream:
                json.dump(stats, stream, ensure_ascii=False, indent=2)
            data = {'output': str(args.output.absolute()), 'stats': stats}
        payload = dict(schema_version=1, command=command, ok=True, data=data, error=None)
        code = 0
    except (OSError, ValueError) as error:
        payload = dict(schema_version=1, command=command, ok=False, data=None,
                       error={'code': type(error).__name__, 'message': str(error)})
        code = 1
    if fault == 'stdout-noise':
        print('TextMeter demo banner')
    print(json.dumps(payload, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
