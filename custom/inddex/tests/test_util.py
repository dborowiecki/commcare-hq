from unittest import TestCase

from custom.inddex.utils import MultiSheetReportExport


class MultiSheetReportExportTest(TestCase):

    def test_getting_table(self):
        report = MultiSheetReportExport(
                title='Report',
                table_data=[
                    ('sheet 1',
                     [
                         ['row11', 'row12'],
                         ['row21', 'row22']
                     ]),
                    ('sheet 2',
                     [
                         ['row11', 'row12'],
                         ['row21', 'row22']
                     ])
                ]
        )
        actual = [
                    [
                        'sheet 1',
                        [
                             ['row11', 'row12'],
                             ['row21', 'row22']
                        ]
                    ],
                    [
                        'sheet 2',
                        [
                            ['row11', 'row12'],
                            ['row21', 'row22']
                        ]
                    ]
                   ]
        
        self.assertEqual(actual, report.get_table())
