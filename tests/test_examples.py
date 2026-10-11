"""不啟動外部軟體的資料規則與幾何邊界測試。"""
import csv
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


report = load('report_example', 'ch05/build_report.py')
images = load('images_example', 'ch06/make_variants.py')


class RegistrationTests(unittest.TestCase):
    def records(self):
        with (ROOT / 'ch05/registrations.csv').open(encoding='utf-8-sig', newline='') as stream:
            return list(csv.DictReader(stream))

    def test_supplied_data_conserves_rows_and_totals(self):
        clean, issues, duplicates = report.classify(self.records())
        self.assertEqual((len(clean), len(issues), len(duplicates)), (4, 3, 1))
        self.assertEqual(sum(row['金額'] for row in clean), 5400)
        self.assertEqual(sum(row['金額'] for row in clean if row['付款狀態'] == '已付款'), 3900)
        self.assertEqual(clean[0]['報名編號'], '001')

    def test_conflicting_id_quarantines_entire_group(self):
        first = self.records()[0]
        conflict = dict(first, 付款狀態='未付款')
        clean, issues, duplicates = report.classify([first, conflict])
        self.assertEqual((len(clean), len(issues), len(duplicates)), (0, 2, 0))

    def test_amount_rejects_ambiguous_and_out_of_range_values(self):
        self.assertEqual(report.amount('1,200'), 1200)
        self.assertEqual(report.amount('1000000000'), 1000000000)
        for value in ['', '0', '-1', '12,00', '1.5', 'NaN', '1000000001']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                report.amount(value)

    def test_correction_exercise(self):
        records = self.records()
        for row in records:
            if row['報名編號'] == '004':
                row['金額'] = '1500'
            elif row['報名編號'] == '005':
                row['金額'] = '1200'
            elif row['報名編號'] == '007':
                row['付款狀態'] = '未付款'
        clean, issues, duplicates = report.classify(records)
        self.assertEqual((len(clean), len(issues), len(duplicates)), (7, 0, 1))
        self.assertEqual(sum(row['金額'] for row in clean), 9300)
        self.assertEqual(sum(row['金額'] for row in clean if row['付款狀態'] == '已付款'), 5400)


class ImagePlanTests(unittest.TestCase):
    def test_landscape_has_expected_crop_and_padding(self):
        web, square, padded = images.plan(1600, 1000)
        self.assertEqual(web['size'], [800, 500])
        self.assertEqual(square['crop_box'], [300, 0, 1300, 1000])
        self.assertEqual(padded['content_size'], [400, 250])

    def test_portrait_keeps_aspect_ratio_and_crops_vertically(self):
        web, square, padded = images.plan(1000, 1600)
        self.assertEqual(web['size'], [800, 1280])
        self.assertEqual(square['crop_box'], [0, 300, 1000, 1300])
        self.assertEqual(padded['content_size'], [250, 400])

    def test_rejects_upscaling(self):
        for size in [(799, 1000), (1600, 599)]:
            with self.subTest(size=size), self.assertRaises(ValueError):
                images.plan(*size)


if __name__ == '__main__':
    unittest.main()
