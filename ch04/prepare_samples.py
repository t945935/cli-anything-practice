"""建立第四章練習文件；不覆寫已存在的 samples 資料夾。"""
from pathlib import Path
import subprocess

base = Path(__file__).resolve().parent
samples = base / 'samples'
samples.mkdir(exist_ok=False)
drafts = base / 'drafts'
drafts.mkdir(exist_ok=True)
cli = 'cli-anything-libreoffice'
documents = [
    ('會議紀錄', 'odt', '課程規劃會議', '決議：下週三完成教材初稿，週五檢查圖片與參考資料。'),
    ('會議紀錄', 'docx', '課程規劃會議修訂版', '決議：新增練習題，並安排週四進行試教。'),
    ('每週工作 報告', 'docx', '本週工作報告', '完成項目：整理文件、更新課程圖片，以及確認電子書目錄。'),
]
for name, fmt, title, paragraph in documents:
    project = drafts / (name + '.' + fmt + '.json')
    commands = [
        [cli, 'document', 'new', '--type', 'writer', '--name', title, '-o', str(project)],
        [cli, '--project', str(project), 'writer', 'add-heading', '--text', title],
        [cli, '--project', str(project), 'writer', 'add-paragraph', '--text', paragraph],
        [cli, '--project', str(project), 'export', 'render', str(samples / (name + '.' + fmt)), '--preset', fmt],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
(samples / '損壞範例.odt').write_bytes(b'This is intentionally not an ODF ZIP file.\n')
(samples / '說明.txt').write_text('練習資料：三份有效文件、一份刻意損壞的 ODT，以及本說明。\n', encoding='utf-8')
print(samples)
