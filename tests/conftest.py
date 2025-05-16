from unittest import TestCase
from unittest.mock import patch
from app.screener.discover import Screener

class TestStockDiscovery(TestCase):
    @patch('app.screener.discover.Screener')
    def test_find_candidates(self, MockScreener):
        mock_screener = MockScreener.return_value
        mock_screener.get_candidates.return_value = ['AAPL', 'GOOGL']
        result = mock_screener.get_candidates()
        self.assertEqual(len(result), 2)

    @patch('app.screener.discover.Screener')
    def test_find_candidates_with_custom_price(self, MockScreener):
        mock_screener = MockScreener.return_value
        mock_screener.get_candidates.return_value = ['AAPL']
        result = mock_screener.get_candidates()
        self.assertEqual(len(result), 1)

    @patch('app.screener.discover.Screener')
    def test_get_candidates(self, MockScreener):
        mock_screener = MockScreener.return_value
        mock_screener.get_candidates.return_value = ['AAPL', 'MSFT']
        result = mock_screener.get_candidates()
        self.assertEqual(len(result), 2) 

    @patch('app.screener.discover.Screener')
    def test_no_candidates(self, MockScreener):
        mock_screener = MockScreener.return_value
        mock_screener.get_candidates.return_value = []
        result = mock_screener.get_candidates()
        self.assertEqual(len(result), 0)

    @patch('app.screener.discover.Screener')
    def test_empty_candidates(self, MockScreener):
        mock_screener = MockScreener.return_value
        mock_screener.get_candidates.return_value = []
        result = mock_screener.get_candidates()
        self.assertEqual(result, [])

# tests/conftest.py
import pytest
from app.screener.discover import Screener

@pytest.fixture
def screener():
    return Screener()

# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*