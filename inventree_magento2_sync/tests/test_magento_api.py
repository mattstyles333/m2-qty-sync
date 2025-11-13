"""Tests for Magento 2 API client."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from inventree_magento2_sync.magento_api import Magento2APIError, Magento2Client


class TestMagento2Client(unittest.TestCase):
    """Test cases for Magento2Client."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://example.com"
        self.access_token = "test_token_123"
        self.client = Magento2Client(
            base_url=self.base_url,
            access_token=self.access_token,
            timeout=10,
        )

    def test_client_initialization(self):
        """Test client is initialized correctly."""
        self.assertEqual(self.client.base_url, self.base_url)
        self.assertEqual(self.client.access_token, self.access_token)
        self.assertEqual(self.client.timeout, 10)
        self.assertTrue(self.client.verify_ssl)

    def test_headers_set_correctly(self):
        """Test authorization headers are set."""
        headers = self.client.session.headers
        self.assertEqual(headers["Authorization"], f"Bearer {self.access_token}")
        self.assertEqual(headers["Content-Type"], "application/json")

    @patch("inventree_magento2_sync.magento_api.requests.Session.request")
    def test_get_product_by_sku_success(self, mock_request):
        """Test successful product retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"sku": "TEST-SKU", "name": "Test Product"}'
        mock_response.json.return_value = {
            "sku": "TEST-SKU",
            "name": "Test Product",
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = self.client.get_product_by_sku("TEST-SKU")

        self.assertIsNotNone(result)
        self.assertEqual(result["sku"], "TEST-SKU")
        mock_request.assert_called_once()

    @patch("inventree_magento2_sync.magento_api.requests.Session.request")
    def test_get_product_not_found(self, mock_request):
        """Test product not found returns None."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Product not found"
        mock_response.raise_for_status = Mock(
            side_effect=Exception("404 Client Error")
        )
        mock_request.return_value = mock_response

        result = self.client.get_product_by_sku("NONEXISTENT")

        # Should return None for 404, not raise exception
        self.assertIsNone(result)

    @patch("inventree_magento2_sync.magento_api.requests.Session.request")
    def test_update_product_stock_success(self, mock_request):
        """Test successful stock update."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "1"
        mock_response.json.return_value = 1
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = self.client.update_product_stock("TEST-SKU", 100)

        self.assertTrue(result)
        mock_request.assert_called_once()

        # Verify the payload structure
        call_args = mock_request.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["stockItem"]["qty"], 100)
        self.assertTrue(payload["stockItem"]["is_in_stock"])

    @patch("inventree_magento2_sync.magento_api.requests.Session.request")
    def test_update_product_stock_out_of_stock(self, mock_request):
        """Test stock update with zero quantity."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "1"
        mock_response.json.return_value = 1
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = self.client.update_product_stock("TEST-SKU", 0)

        self.assertTrue(result)

        # Verify is_in_stock is False for zero quantity
        call_args = mock_request.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["stockItem"]["qty"], 0)
        self.assertFalse(payload["stockItem"]["is_in_stock"])

    @patch("inventree_magento2_sync.magento_api.requests.Session.request")
    def test_connection_error(self, mock_request):
        """Test handling of connection errors."""
        import requests

        mock_request.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        with self.assertRaises(Magento2APIError) as context:
            self.client.get_product_by_sku("TEST-SKU")

        self.assertIn("Connection error", str(context.exception))

    @patch("inventree_magento2_sync.magento_api.requests.Session.request")
    def test_timeout_error(self, mock_request):
        """Test handling of timeout errors."""
        import requests

        mock_request.side_effect = requests.exceptions.Timeout("Request timed out")

        with self.assertRaises(Magento2APIError) as context:
            self.client.get_product_by_sku("TEST-SKU")

        self.assertIn("timeout", str(context.exception).lower())

    @patch("inventree_magento2_sync.magento_api.requests.Session.request")
    def test_test_connection_success(self, mock_request):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "[]"
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = self.client.test_connection()

        self.assertTrue(result)

    @patch("inventree_magento2_sync.magento_api.requests.Session.request")
    def test_test_connection_failure(self, mock_request):
        """Test failed connection test."""
        import requests

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status = Mock(
            side_effect=requests.exceptions.HTTPError()
        )
        mock_request.return_value = mock_response

        with self.assertRaises(Magento2APIError):
            self.client.test_connection()


if __name__ == "__main__":
    unittest.main()
