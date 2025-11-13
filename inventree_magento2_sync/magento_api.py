"""Magento 2 API client for stock synchronization."""

import logging
from typing import Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("inventree")


class Magento2APIError(Exception):
    """Custom exception for Magento 2 API errors."""

    pass


class Magento2Client:
    """Client for interacting with Magento 2 REST API."""

    def __init__(
        self,
        base_url: str,
        access_token: str,
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """Initialize Magento 2 API client.

        Args:
            base_url: Magento 2 base URL (e.g., https://example.com)
            access_token: Integration access token
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _make_request(
        self, method: str, endpoint: str, json_data: Optional[dict] = None
    ) -> dict:
        """Make a request to the Magento 2 API.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint (e.g., /rest/V1/products/SKU123)
            json_data: JSON data to send in request body

        Returns:
            Response JSON data

        Raises:
            Magento2APIError: If the API request fails
        """
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Magento 2 API error: {error_msg}")
            raise Magento2APIError(error_msg) from e

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Magento 2 API connection error: {error_msg}")
            raise Magento2APIError(error_msg) from e

        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(f"Magento 2 API timeout: {error_msg}")
            raise Magento2APIError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Magento 2 API unexpected error: {error_msg}")
            raise Magento2APIError(error_msg) from e

    def get_product_by_sku(self, sku: str) -> Optional[dict]:
        """Get product details by SKU.

        Args:
            sku: Product SKU

        Returns:
            Product data dict or None if not found
        """
        try:
            endpoint = f"/rest/V1/products/{sku}"
            return self._make_request("GET", endpoint)
        except Magento2APIError as e:
            if "404" in str(e):
                logger.warning(f"Product with SKU '{sku}' not found in Magento 2")
                return None
            raise

    def update_product_stock(
        self, sku: str, quantity: float, is_in_stock: Optional[bool] = None
    ) -> bool:
        """Update product stock quantity in Magento 2.

        Args:
            sku: Product SKU
            quantity: New stock quantity
            is_in_stock: Whether product is in stock (auto-determined if None)

        Returns:
            True if update successful

        Raises:
            Magento2APIError: If the update fails
        """
        # Auto-determine stock status if not specified
        if is_in_stock is None:
            is_in_stock = quantity > 0

        endpoint = f"/rest/V1/products/{sku}/stockItems/1"
        
        payload = {
            "stockItem": {
                "qty": quantity,
                "is_in_stock": is_in_stock,
            }
        }

        try:
            result = self._make_request("PUT", endpoint, json_data=payload)
            logger.info(
                f"Successfully updated Magento 2 stock for SKU '{sku}': "
                f"qty={quantity}, in_stock={is_in_stock}"
            )
            return True

        except Magento2APIError as e:
            logger.error(f"Failed to update stock for SKU '{sku}': {str(e)}")
            raise

    def test_connection(self) -> bool:
        """Test the API connection and authentication.

        Returns:
            True if connection is successful

        Raises:
            Magento2APIError: If connection test fails
        """
        try:
            # Try to get store config as a simple test
            endpoint = "/rest/V1/store/storeConfigs"
            self._make_request("GET", endpoint)
            logger.info("Magento 2 API connection test successful")
            return True
        except Magento2APIError as e:
            logger.error(f"Magento 2 API connection test failed: {str(e)}")
            raise
