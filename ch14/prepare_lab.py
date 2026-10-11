"""將第十四章起始專案複製到新目錄，供 CLI 生成練習使用。"""
import argparse
from pathlib import Path
import shutil


def prepare(output: Path) -> Path:
    source = Path(__file__).resolve().parent / 'textmeter'
    # mkdir(exist_ok=False) 同時拒絕既有目錄、檔案或符號連結。
    output.mkdir(parents=True, exist_ok=False)
    target = output / 'textmeter'
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        '__pycache__', '*.pyc', '*.egg-info', 'build', 'dist', 'agent-harness'))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(f'已準備起始專案：{prepare(args.output)}')
        return 0
    except OSError as error:
        print(f'準備失敗，請保留現況並檢查路徑：{error}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
