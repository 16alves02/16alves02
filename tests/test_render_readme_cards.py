import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_readme_cards as cards


class ContributionParserTests(unittest.TestCase):
    def test_parses_attribute_order_and_tooltip(self):
        source = '''
        <table>
          <tr>
            <td class="ContributionCalendar-day" data-level="2" data-date="2026-11-18">
              <tool-tip aria-label="3 contributions on November 18th, 2026"></tool-tip>
            </td>
            <td data-date="2026-11-19" data-count="0" data-level="0"></td>
          </tr>
        </table>
        '''
        self.assertEqual(cards.parse_contribution_html(source), [
            {"date": "2026-11-18", "count": 3, "level": 2},
            {"date": "2026-11-19", "count": 0, "level": 0},
        ])

    def test_no_contributions_tooltip(self):
        source = '<td data-date="2026-11-19" data-level="0"><tool-tip>No contributions on November 19th</tool-tip></td>'
        self.assertEqual(cards.parse_contribution_html(source), [
            {"date": "2026-11-19", "count": 0, "level": 0},
        ])

    def test_stats(self):
        days = [
            {"date": "2026-11-17", "count": 2, "level": 1},
            {"date": "2026-11-18", "count": 5, "level": 2},
            {"date": "2026-11-19", "count": 0, "level": 0},
        ]
        total, active, best, best_date, streak, months = cards.contribution_stats(days)
        self.assertEqual((total, active, best, best_date), (7, 2, 5, "2026-11-18"))
        self.assertEqual(months["2026-11"], 7)


if __name__ == "__main__":
    unittest.main()
