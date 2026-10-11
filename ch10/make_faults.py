"""複製教材並故意製造一種錯誤，原始成品保持不變。"""
import argparse
from pathlib import Path
import shutil
import zipfile
from defusedxml import ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=['missing-file', 'broken-pptx', 'wrong-text', 'wrong-image'], required=True)
    args = parser.parse_args()
    source, output = args.artifacts.resolve(), args.output.resolve()
    if not source.is_dir() or args.output.exists() or args.output.is_symlink() or source == output or source in output.parents:
        parser.error('來源須存在，輸出須為來源以外的新目錄')
    if any(path.is_symlink() for path in source.rglob('*')):
        parser.error('本練習不接受含符號連結的素材目錄')
    shutil.copytree(source, output)
    if args.case == 'missing-file':
        (output / 'handout.pdf').unlink()
    elif args.case == 'broken-pptx':
        (output / 'slides.pptx').write_bytes(b'This is intentionally not a PPTX file.\n')
    elif args.case == 'wrong-image':
        # 換成另一個既有檔案；副檔名是 PNG，實際內容仍是 JPEG。
        shutil.copyfile(output / 'assets/web.jpg', output / 'assets/square.png')
    else:
        pptx = output / 'slides.pptx'
        with zipfile.ZipFile(pptx) as archive:
            contents = {name: archive.read(name) for name in archive.namelist()}
        for name, content in list(contents.items()):
            if name.startswith('ppt/slides/slide') and name.endswith('.xml'):
                root = ET.fromstring(content)
                for node in root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
                    node.text = '這是刻意替換的錯誤文字'
                contents[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        with zipfile.ZipFile(pptx, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in contents.items():
                archive.writestr(name, content)
    print(f'已建立錯誤副本：{output}（{args.case}）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
