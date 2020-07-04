import unittest
from copy import deepcopy

import shell_cov.shell_cov as shell_cov

ACTUAL_LINES = {
    'script1': set(range(10)),
    'script2': set(range(0, 20, 2))
}


class TestOutput(unittest.TestCase):
    def test_determine_display_widths(self):
        values = [
            ['2' * 2, '3' * 3, '5' * 5, '4' * 4, '9' * 9],
            ['s' * 5, 'l' * 14, 'a', 'h' * 10, 'g' * 25],
            ['a', 'b' * 3, 'c' * 3, 'f' * 5, 'w' * 10]
        ]
        expect_widths = [5, 14, 5, 10, 25]
        expect_header = [5, 14, 5, 10, 9]
        widths, header = shell_cov.determine_display_widths(values)
        self.assertEqual(widths, expect_widths)
        self.assertEqual(header, expect_header)

    def test_get_line_info_no_problem_perfect_coverage(self):
        seen = deepcopy(ACTUAL_LINES)

        expected_values = [
            shell_cov.COLUMN_HEADINGS,
            ['script1', str(len(ACTUAL_LINES['script1'])), '0', '100%', ''],
            ['script2', str(len(ACTUAL_LINES['script2'])), '0', '100%', '']
        ]
        expected_problems = {'script1': set(), 'script2': set()}

        values, problems = shell_cov.get_line_info(ACTUAL_LINES, seen)
        self.assertEqual(values, expected_values)
        self.assertEqual(problems, expected_problems)

    def test_get_line_info_no_problem_no_coverage(self):
        seen = {'script1': set(), 'script2': set()}

        expected_values = [
            shell_cov.COLUMN_HEADINGS,
            ['script1', str(len(ACTUAL_LINES['script1'])),
             str(len(ACTUAL_LINES['script1'])), '0%',
             ','.join(str(s) for s in ACTUAL_LINES['script1'])],
            ['script2', str(len(ACTUAL_LINES['script1'])),
             str(len(ACTUAL_LINES['script2'])), '0%',
             ','.join(str(s) for s in ACTUAL_LINES['script2'])]
        ]
        expected_problems = deepcopy(seen)

        values, problems = shell_cov.get_line_info(ACTUAL_LINES, seen)
        self.assertEqual(values, expected_values)
        self.assertEqual(problems, expected_problems)

    def test_get_line_info_all_problems_no_coverage(self):
        seen = {
            'script1': set(range(20, 30)),
            'script2': set(range(99, 120, 3))
        }

        expected_values = [
            shell_cov.COLUMN_HEADINGS,
            ['script1', str(len(ACTUAL_LINES['script1'])),
             str(len(ACTUAL_LINES['script1'])), '0%',
             ','.join(str(s) for s in ACTUAL_LINES['script1'])],
            ['script2', str(len(ACTUAL_LINES['script1'])),
             str(len(ACTUAL_LINES['script2'])), '0%',
             ','.join(str(s) for s in ACTUAL_LINES['script2'])]
        ]
        expected_problems = deepcopy(seen)

        values, problems = shell_cov.get_line_info(ACTUAL_LINES, seen)
        self.assertEqual(values, expected_values)
        self.assertEqual(problems, expected_problems)

    def test_get_line_info_some_problems_some_coverage(self):
        seen = {
            'script1': set(range(5, 15)),
            'script2': set(range(15, 20))
        }

        expected_values = [
            shell_cov.COLUMN_HEADINGS,
            ['script1', str(len(ACTUAL_LINES['script1'])),
             '5', '50%',
             ','.join(str(s) for s in range(5))],
            ['script2', str(len(ACTUAL_LINES['script1'])),
             '8', '20%',
             ','.join(str(s) for s in range(0, 15, 2))]
        ]
        expected_problems = {
            'script1': set(range(10, 15)),
            'script2': {15, 17, 19}
        }

        values, problems = shell_cov.get_line_info(ACTUAL_LINES, seen)
        self.assertEqual(values, expected_values)
        self.assertEqual(problems, expected_problems)
