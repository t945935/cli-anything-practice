"""第十一章：依序執行每週文件、資料、教材與品質檢查，保存各階段結果。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def counts_valid(counts, keys):
    return isinstance(counts, dict) and all(type(counts.get(key)) is int and counts[key] >= 0 for key in keys)


def document_status(code, counts):
    if not counts_valid(counts, ['passed_basic_checks', 'failed', 'skipped']):
        raise ValueError('文件報告筆數格式錯誤')
    passed, failed = counts['passed_basic_checks'], counts['failed']
    if passed + failed == 0 or code != (1 if failed else 0):
        raise ValueError('文件報告與結束碼不一致或沒有處理文件')
    return 'partial_failure' if failed and passed else 'failed' if failed else 'passed'


def registration_status(code, summary, verification):
    counts = summary.get('counts')
    if not counts_valid(counts, ['input', 'valid', 'issues', 'duplicates']):
        raise ValueError('報名資料筆數格式錯誤')
    if counts['input'] == 0 or counts['input'] != sum(counts[key] for key in ['valid', 'issues', 'duplicates']):
        raise ValueError('報名資料分類筆數不一致')
    if code != (3 if counts['issues'] else 0):
        raise ValueError('報名資料結束碼與待查筆數不一致')
    for key in ['all_written_cells_verified', 'totals_are_verified_numeric_values', 'registration_ids_remain_text', 'source_unchanged']:
        if verification.get(key) is not True:
            raise ValueError('報名成果缺少已通過的驗證：' + key)
    return 'needs_review' if counts['issues'] else 'passed'


def overall(stages):
    statuses = {row['status'] for row in stages}
    if statuses & {'failed', 'blocked'}:
        return 'failed', 1
    if statuses & {'partial_failure', 'needs_review'}:
        return 'attention_required', 3
    return 'needs_review', 0


def prepare(config, output):
    data = read_json(config)
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('設定檔 schema_version 必須為整數 1')
    if not isinstance(data.get('label'), str) or not data['label'].strip():
        raise ValueError('設定檔需有非空白 label')
    paths = {}
    for key in ['documents', 'registrations', 'lesson']:
        if not isinstance(data.get(key), str) or not data[key]:
            raise ValueError('設定檔缺少路徑：' + key)
        paths[key] = (config.parent / data[key]).resolve()
    if not paths['documents'].is_dir() or not all(paths[key].is_file() for key in ['registrations', 'lesson']):
        raise ValueError('來源文件資料夾、CSV 或課程 JSON 不存在')
    documents = sorted(paths['documents'].iterdir())
    if not documents or any(not p.is_file() or p.is_symlink() for p in documents):
        raise ValueError('本章文件資料夾須非空，且第一層只能包含普通檔案')
    if not any(p.suffix.lower() in {'.docx', '.odt'} and not p.name.startswith('~$') for p in documents):
        raise ValueError('找不到可處理的 DOCX／ODT')
    if output == paths['documents'] or paths['documents'] in output.parents:
        raise ValueError('輸出不可位於來源文件資料夾內')
    files = [config, *documents, paths['registrations'], paths['lesson']]
    manifest = {str(p): sha(p) for p in files}
    return data, paths, documents, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    config, output = args.config.resolve(), args.output.resolve()
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('輸出目錄已存在，請使用新的週次或執行版本名稱')
        data, paths, documents, manifest = prepare(config, output)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps({'label': data['label'], 'input_paths': {k: str(v) for k, v in paths.items()},
                          'document_files': [p.name for p in documents], 'output': str(output),
                          'order': ['documents', 'registrations', 'lesson_job', 'quality'],
                          'dependencies': {'quality': ['lesson_job']}, 'scheduled': False}, ensure_ascii=False, indent=2))
        return 0
    output.mkdir(parents=True)
    (output / 'logs').mkdir()
    inputs = output / 'inputs'
    (inputs / 'documents').mkdir(parents=True)
    for path in documents:
        (inputs / 'documents' / path.name).write_bytes(path.read_bytes())
    for key, name in [('registrations', 'registrations.csv'), ('lesson', 'lesson.json')]:
        (inputs / name).write_bytes(paths[key].read_bytes())
    (inputs / 'weekly.json').write_bytes(config.read_bytes())
    expected_snapshots = {'weekly.json': manifest[str(config)], 'registrations.csv': manifest[str(paths['registrations'])],
                          'lesson.json': manifest[str(paths['lesson'])],
                          **{'documents/' + p.name: manifest[str(p)] for p in documents}}
    if any(sha(inputs / name) != digest for name, digest in expected_snapshots.items()):
        raise ValueError('來源在建立快照時改變，請保留此資料夾並用新目錄重跑')
    write_json(inputs / 'manifest.json', {'sources': manifest, 'snapshot_sha256': expected_snapshots})
    report = {'schema_version': 1, 'label': data['label'], 'started_at': datetime.now(timezone.utc).isoformat(),
              'status': 'running', 'needs_visual_review': True, 'stages': [], 'current_step': None}

    def save():
        write_json(output / 'weekly.json', report)
        lines = ['# 每週工作彙整', '', data['label'].replace('\n', ' '), '',
                 f"整體狀態：`{report['status']}`；仍需人工檢查。", '',
                 '| 階段 | 狀態 | 結束碼 | 摘要 |', '| --- | --- | --- | --- |']
        for row in report['stages']:
            detail = str(row.get('detail', '')).replace('|', '\\|').replace('\n', ' ')
            lines.append(f"| {row['name']} | {row['status']} | {row.get('exit_code', '—')} | {detail} |")
        lines += ['', '## 成果位置', '', '- 文件：`documents/`', '- 報名資料：`registrations/`',
                  '- 教材工作：`lesson-job/`', '- 教材品質報告：`quality/`', '- 命令紀錄：`logs/`', '',
                  '失敗或被阻擋的階段可能沒有完整成果。此流程未設定排程，也不會發布或寄送檔案。', '']
        (output / 'weekly.md').write_text('\n'.join(lines), encoding='utf-8')

    def stage(name, command, evaluate):
        report['current_step'] = name
        save()
        row = {'name': name, 'status': 'failed'}
        try:
            result = subprocess.run(list(map(str, command)), capture_output=True, text=True)
            row['exit_code'] = result.returncode
            write_json(output / 'logs' / (name + '.json'), {'args': list(map(str, command)), 'returncode': result.returncode,
                                                         'stdout': result.stdout, 'stderr': result.stderr})
            row['status'], row['detail'] = evaluate(result.returncode)
        except Exception as error:
            row['detail'] = f'{type(error).__name__}: {error}'
        report['stages'].append(row)
        save()
        return row['status']

    def documents_result(code):
        result = read_json(output / 'documents/report.json')
        counts, rows = result['counts'], result['files']
        status = document_status(code, counts)
        if not isinstance(rows, list) or len(rows) != len(documents):
            raise ValueError('文件明細與輸入檔案數量不一致')
        if sorted(row['input'] for row in rows) != sorted(p.name for p in documents):
            raise ValueError('文件報告的檔案名稱不符')
        for key in ['passed_basic_checks', 'failed', 'skipped']:
            if sum(row['status'] == key for row in rows) != counts[key]:
                raise ValueError('文件明細與彙總筆數不一致')
        for row in rows:
            if row['status'] == 'passed_basic_checks':
                if row.get('source_unchanged') is not True or not (output / 'documents/pdf' / (row['input'] + '.pdf')).read_bytes().startswith(b'%PDF-'):
                    raise ValueError('通過的文件缺少 PDF 或來源驗證')
        return status, counts

    def registrations_result(code):
        summary = read_json(output / 'registrations/summary.json')
        verification = read_json(output / 'registrations/verification.json')
        status = registration_status(code, summary, verification)
        if summary['input_sha256'] != expected_snapshots['registrations.csv']:
            raise ValueError('報名報表未對應本次輸入')
        for fmt in ['ods', 'xlsx']:
            with zipfile.ZipFile(output / f'registrations/report.{fmt}') as archive:
                if archive.testzip() is not None:
                    raise ValueError('試算表 ZIP 檢查失敗')
        return status, {'counts': summary['counts'], 'totals': summary['totals']}

    def lesson_result(code):
        state = read_json(output / 'lesson-job/state.json')
        if code != 0 or state['status'] != 'needs_review' or state['input_sha256'] != expected_snapshots['lesson.json']:
            raise ValueError('教材工作未完成基本驗證：' + str(state.get('error')))
        return 'passed', '教材工作已到達 needs_review；品質檢查接續執行'

    def quality_result(code):
        quality = read_json(output / 'quality/report.json')
        checks, counts = quality['checks'], quality['counts']
        if len(checks) != 11 or any(sum(row['status'] == key for row in checks) != counts[key] for key in ['passed', 'failed', 'blocked']):
            raise ValueError('品質報告檢查項目不完整或數量不一致')
        expected = ('failed', 1) if counts['failed'] else ('incomplete', 2) if counts['blocked'] else ('passed_basic_checks', 0)
        if (quality['status'], code) != expected or quality['input_sha256'] != expected_snapshots['lesson.json']:
            raise ValueError('品質報告、來源或結束碼不一致')
        status = 'failed' if counts['failed'] else 'blocked' if counts['blocked'] else 'passed'
        return status, counts

    python = sys.executable
    stage('documents', [python, ROOT / 'ch04/batch_convert.py', '--input', inputs / 'documents', '--output', output / 'documents'], documents_result)
    stage('registrations', [python, ROOT / 'ch05/build_report.py', '--input', inputs / 'registrations.csv', '--output', output / 'registrations'], registrations_result)
    lesson_status = stage('lesson_job', [python, ROOT / 'ch09/run_job.py', 'start', '--input', inputs / 'lesson.json',
                                       '--workspace', ROOT, '--job-dir', output / 'lesson-job'], lesson_result)
    if lesson_status == 'passed':
        stage('quality', [python, ROOT / 'ch10/audit_lesson.py', '--input', inputs / 'lesson.json',
                          '--artifacts', output / 'lesson-job/attempt-001/artifacts', '--report-dir', output / 'quality'], quality_result)
    else:
        report['stages'].append({'name': 'quality', 'status': 'blocked', 'detail': '教材工作未完成，未啟動品質檢查'})
    try:
        stable = all(sha(Path(path)) == value for path, value in manifest.items())
        stable = stable and sorted(p.name for p in paths['documents'].iterdir()) == sorted(p.name for p in documents)
        stable = stable and all(sha(inputs / name) == value for name, value in expected_snapshots.items())
    except OSError:
        stable = False
    report['stages'].append({'name': 'inputs', 'status': 'passed' if stable else 'failed',
                             'detail': '原始來源及快照的前後雜湊觀測一致' if stable else '來源或快照在執行期間改變'})
    report['status'], code = overall(report['stages'])
    report.update(current_step=None, finished_at=datetime.now(timezone.utc).isoformat())
    save()
    print(json.dumps({'status': report['status'], 'stages': report['stages'], 'summary': str(output / 'weekly.md')}, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())
