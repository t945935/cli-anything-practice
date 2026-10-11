"""第五章：明確規則清理 CSV，透過 LibreOffice CLI 建立並驗證 XLSX。

結束碼：0 完成且無待查資料；3 成果已產生但仍有待查資料；1 執行失敗；2 參數錯誤。
金額限正整數新臺幣，每筆不超過十億元；不處理退款、折扣或部分付款。
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
from defusedxml import ElementTree as ET

FIELDS = ['報名編號', '姓名', '課程', '金額', '付款狀態']


def amount(value):
    if not re.fullmatch(r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)', value):
        raise ValueError('金額必須是正整數，可含正確的千分位逗號')
    result = int(value.replace(',', ''))
    if not 0 < result <= 1_000_000_000:
        raise ValueError('金額必須介於 1 與 1,000,000,000 元')
    return result


def classify(records):
    groups = defaultdict(list)
    clean, issues, duplicates = [], [], []
    for index, record in enumerate(records, 1):
        raw = {field: record[field] for field in FIELDS}
        item = {field: raw[field].strip() for field in FIELDS}
        item.update(來源筆次=index, 原始資料=raw)
        if not item['報名編號']:
            issues.append(dict(item, 原因='缺少報名編號'))
        else:
            groups[item['報名編號']].append(item)
    for group in groups.values():
        # 同編號若欄位不一致，整組待查，不自行挑選版本。
        if len({tuple(item[field] for field in FIELDS) for item in group}) > 1:
            issues.extend(dict(item, 原因='相同報名編號的內容不一致') for item in group)
            continue
        item = group[0]
        try:
            if not item['姓名'] or not item['課程']:
                raise ValueError('姓名與課程不可空白')
            number = amount(item['金額'])
            if item['付款狀態'] not in {'已付款', '未付款'}:
                raise ValueError('付款狀態只能是已付款或未付款')
        except ValueError as error:
            issues.extend(dict(row, 原因=str(error)) for row in group)
            continue
        clean.append(dict(item, 金額=number))
        duplicates.extend(dict(row, 原因=f"與第 {item['來源筆次']} 筆重複") for row in group[1:])
    for rows in [clean, issues, duplicates]:
        rows.sort(key=lambda item: item['來源筆次'])
    return clean, issues, duplicates


def write_csv(path, headers, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def verify_xlsx(path, grids):
    """讀取 LibreOffice 輸出的 XLSX，不以專案 JSON 代替成品驗證。"""
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('XLSX ZIP 檢查失敗')
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        names = [node.attrib['name'] for node in workbook.findall('s:sheets/s:sheet', ns)]
        if names != [name for name, _ in grids]:
            raise ValueError('XLSX 工作表清單不符')
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            strings = [''.join(n.itertext()) for n in root.findall('s:si', ns)]
        for sheet_index, (_, rows) in enumerate(grids, 1):
            root = ET.fromstring(archive.read(f'xl/worksheets/sheet{sheet_index}.xml'))
            cells = {node.attrib['r']: node for node in root.findall('.//s:c', ns)}
            for row_index, row in enumerate(rows, 1):
                for col_index, expected in enumerate(row):
                    ref = f'{chr(65 + col_index)}{row_index}'
                    cell = cells.get(ref)
                    if cell is None:
                        if expected == '':
                            continue
                        raise ValueError(f'缺少儲存格：{sheet_index}:{ref}')
                    value = cell.findtext('s:v', default='', namespaces=ns)
                    kind = cell.attrib.get('t', 'n')
                    if isinstance(expected, int):
                        if kind != 'n' or float(value) != expected:
                            raise ValueError(f'數值驗證失敗：{sheet_index}:{ref}')
                    else:
                        actual = strings[int(value)] if kind == 's' else ''.join(cell.find('s:is', ns).itertext()) if kind == 'inlineStr' else value
                        if actual != expected or (expected and kind not in {'s', 'inlineStr', 'str'}):
                            raise ValueError(f'文字驗證失敗：{sheet_index}:{ref}')
    return {'sheets': names, 'all_written_cells_verified': True,
            'totals_are_verified_numeric_values': True, 'registration_ids_remain_text': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true', help='只讀取並分類，不寫檔')
    args = parser.parse_args()
    source, output = args.input.resolve(), args.output.resolve()
    try:
        initial_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        with source.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream, strict=True)
            if reader.fieldnames != FIELDS:
                parser.error('CSV 欄位與順序必須是：' + ','.join(FIELDS))
            records = list(reader)
        if not records or any(None in row or any(v is None for v in row.values()) for row in records):
            parser.error('CSV 必須有資料，且每筆欄位數正確')
    except (OSError, UnicodeError, csv.Error) as error:
        parser.error(str(error))
    clean, issues, duplicates = classify(records)
    counts = {'input': len(records), 'valid': len(clean), 'issues': len(issues), 'duplicates': len(duplicates)}
    if sum(counts[k] for k in ['valid', 'issues', 'duplicates']) != counts['input']:
        raise ValueError('分類筆數不一致')
    if args.check_only:
        print(json.dumps(counts, ensure_ascii=False, indent=2))
        return 3 if issues else 0
    if output.exists():
        parser.error('輸出資料夾已存在，請換新名稱')
    for command in ['cli-anything-libreoffice', 'libreoffice']:
        if not shutil.which(command):
            parser.error(f'找不到 {command}，請啟用本書環境')
    output.mkdir(parents=True)
    course_data = defaultdict(lambda: [0, 0, 0, 0])
    for item in clean:
        value = item['金額']
        row = course_data[item['課程']]
        row[0] += 1
        row[1] += value
        row[2 if item['付款狀態'] == '已付款' else 3] += value
    totals = [sum(row[i] for row in course_data.values()) for i in range(4)]
    summary_rows = [['課程', '筆數', '總額', '已付款', '未付款']]
    summary_rows += [[course, *values] for course, values in sorted(course_data.items())]
    summary_rows.append(['合計', *totals])
    detail_headers = FIELDS + ['來源筆次']
    clean_rows = [[item[field] for field in detail_headers] for item in clean]
    audit_headers = detail_headers + ['原因']
    def audit_rows(items):
        return [[*(item['原始資料'][field] for field in FIELDS), item['來源筆次'], item['原因']] for item in items]
    issue_rows, duplicate_rows = audit_rows(issues), audit_rows(duplicates)
    write_csv(output / 'clean.csv', detail_headers, clean_rows)
    write_csv(output / 'issues.csv', audit_headers, issue_rows)
    write_csv(output / 'duplicates.csv', audit_headers, duplicate_rows)
    summary = {'counts': counts, 'totals': dict(zip(['registrations', 'amount', 'paid', 'unpaid'], totals)),
               'scope': '僅統計有效且去重後資料；待查資料未納入', 'input_sha256': initial_hash,
               'needs_review': bool(issues), 'calculation_scope': 'Python 計算後輸出數值快照；不是連動明細的即時報表'}
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    grids = [('課程彙總', summary_rows), ('有效明細', [detail_headers, *clean_rows]),
             ('待查資料', [audit_headers, *issue_rows]), ('重複紀錄', [audit_headers, *duplicate_rows])]
    project = output / 'report.json'
    log = []
    def run(args):
        result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=180)
        log.append({'args': [str(x) for x in args], 'exit_code': result.returncode,
                    'stdout': result.stdout, 'stderr': result.stderr})
        (output / 'commands.json').write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
    cli = 'cli-anything-libreoffice'
    run([cli, 'document', 'new', '--type', 'calc', '--name', '課程報名檢查報表', '-o', project])
    for sheet, (name, rows) in enumerate(grids):
        if sheet == 0:
            run([cli, '--project', project, 'calc', 'rename-sheet', '0', name])
        else:
            run([cli, '--project', project, 'calc', 'add-sheet', '--name', name])
        for row_number, row in enumerate(rows, 1):
            for col_number, value in enumerate(row):
                col = chr(65 + col_number)
                command = [cli, '--project', project, 'calc', 'set-cell', '--sheet', sheet,
                           '--type', 'float' if isinstance(value, int) else 'string']
                command += ['--', f'{col}{row_number}', str(value)]
                run(command)
    for fmt in ['ods', 'xlsx']:
        run([cli, '--project', project, 'export', 'render', output / f'report.{fmt}', '--preset', fmt])
    verified = verify_xlsx(output / 'report.xlsx', grids)
    verified['source_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == initial_hash
    if not verified['source_unchanged']:
        raise ValueError('來源檔案在執行期間改變')
    (output / 'verification.json').write_text(json.dumps(verified, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f'XLSX 已驗證：{output / "report.xlsx"}')
    return 3 if issues else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f'執行失敗：{error}', file=sys.stderr)
        sys.exit(1)
