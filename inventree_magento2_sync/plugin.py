"""InvenTree plugin for synchronizing stock to Magento 2."""

import logging

from plugin import InvenTreePlugin
from plugin.mixins import EventMixin, SettingsMixin

from .magento_api import Magento2APIError, Magento2Client
from .version import PLUGIN_NAME, PLUGIN_SLUG, PLUGIN_TITLE, PLUGIN_VERSION

logger = logging.getLogger("inventree")


class Magento2StockSyncPlugin(EventMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to synchronize InvenTree stock quantities to Magento 2.

    This plugin listens for stock item changes and automatically updates
    the corresponding product quantity in Magento 2.

    The mapping between InvenTree and Magento 2 is:
    - InvenTree Part Name = Magento 2 Product SKU
    - InvenTree total stock quantity = Magento 2 product quantity
    """

    NAME = PLUGIN_NAME
    SLUG = PLUGIN_SLUG
    TITLE = PLUGIN_TITLE
    VERSION = PLUGIN_VERSION

    AUTHOR = "InvenTree Community"
    DESCRIPTION = "Automatically sync stock quantities from InvenTree to Magento 2"
    WEBSITE = "https://github.com/mattstyles333/m2-qty-sync"
    LICENSE = "MIT"

    SETTINGS = {
        "MAGENTO_URL": {
            "name": "Magento 2 URL",
            "description": "Base URL of your Magento 2 store (e.g., https://example.com)",
            "default": "",
            "required": True,
        },
        "ACCESS_TOKEN": {
            "name": "Access Token",
            "description": "Magento 2 Integration Access Token",
            "default": "",
            "required": True,
            "protected": True,
        },
        "ENABLE_SYNC": {
            "name": "Enable Sync",
            "description": "Enable automatic stock synchronization to Magento 2",
            "default": False,
            "validator": bool,
        },
        "DRY_RUN": {
            "name": "Dry Run Mode",
            "description": "Log sync actions without actually updating Magento 2",
            "default": False,
            "validator": bool,
        },
        "VERIFY_SSL": {
            "name": "Verify SSL",
            "description": "Verify SSL certificates when connecting to Magento 2",
            "default": True,
            "validator": bool,
        },
        "TIMEOUT": {
            "name": "Request Timeout",
            "description": "API request timeout in seconds",
            "default": 30,
            "validator": int,
        },
    }

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        logger.info(f"[Magento2StockSync] Plugin v{PLUGIN_VERSION} initialized")

    def get_magento_client(self) -> Magento2Client:
        """Get a Magento 2 API client.

        Returns:
            Configured Magento2Client instance

        Raises:
            ValueError: If required settings are not configured
        """
        magento_url = self.get_setting("MAGENTO_URL")
        access_token = self.get_setting("ACCESS_TOKEN")

        if not magento_url or not access_token:
            raise ValueError(
                "Magento 2 URL and Access Token must be configured in plugin settings"
            )

        return Magento2Client(
            base_url=magento_url,
            access_token=access_token,
            timeout=self.get_setting("TIMEOUT", backup_value=30),
            verify_ssl=self.get_setting("VERIFY_SSL", backup_value=True),
        )

    def wants_process_event(self, event: str) -> bool:
        """Determine if this event should be processed.

        InvenTree triggers events using database table names:
        - stock_stockitem.created - when a new stock item is created
        - stock_stockitem.saved - when a stock item is modified
        - stock_stockitem.deleted - when a stock item is deleted

        Args:
            event: Event name (format: tablename.action)

        Returns:
            True if this is a stock item event we should process
        """
        # Check if sync is enabled first
        sync_enabled = self.get_setting("ENABLE_SYNC", backup_value=False)

        if not sync_enabled:
            return False

        # Stock item events we care about
        # These are the actual event names InvenTree generates
        stock_events = [
            "stock_stockitem.created",
            "stock_stockitem.saved",
            "stock_stockitem.deleted",
        ]

        should_process = event in stock_events

        if should_process:
            logger.debug(f"[Magento2StockSync] Will process event: {event}")

        return should_process

    def process_event(self, event: str, *args, **kwargs):
        """Process a stock change event and sync to Magento 2.

        Args:
            event: Event name
            *args: Positional arguments from event
            **kwargs: Keyword arguments - contains 'model' and 'id'
        """
        logger.info(f"[Magento2StockSync] Processing event: {event}")
        logger.debug(f"[Magento2StockSync] Event kwargs: {kwargs}")

        try:
            # Extract event data - InvenTree passes 'id' and 'model'
            stock_item_id = kwargs.get("id")
            model_name = kwargs.get("model")

            if not stock_item_id:
                logger.warning("[Magento2StockSync] No stock item ID in event data")
                return

            # For delete events, we can't look up the item anymore
            if event == "stock_stockitem.deleted":
                logger.info(
                    f"[Magento2StockSync] Stock item {stock_item_id} deleted - "
                    "cannot sync (item no longer exists)"
                )
                return

            # Import StockItem model and fetch the item
            try:
                from stock.models import StockItem
            except ImportError:
                logger.error("[Magento2StockSync] Could not import stock.models")
                return

            try:
                stock_item = StockItem.objects.get(pk=stock_item_id)
            except StockItem.DoesNotExist:
                logger.warning(
                    f"[Magento2StockSync] StockItem {stock_item_id} not found"
                )
                return

            # Get the associated Part
            part = stock_item.part
            if not part:
                logger.warning(
                    f"[Magento2StockSync] StockItem {stock_item_id} has no associated Part"
                )
                return

            # Use Part name as Magento 2 SKU
            sku = part.name
            if not sku:
                logger.warning(
                    f"[Magento2StockSync] Part {part.pk} has no name, cannot sync"
                )
                return

            # Calculate total available quantity for this Part
            total_quantity = self._calculate_total_quantity(part)

            logger.info(
                f"[Magento2StockSync] Part '{sku}' total quantity: {total_quantity}"
            )

            # Sync to Magento 2
            self._sync_to_magento(sku, total_quantity, event)

        except Exception as e:
            logger.error(
                f"[Magento2StockSync] Error processing event: {e}",
                exc_info=True
            )

    def _calculate_total_quantity(self, part) -> float:
        """Calculate total available quantity for a Part.

        Args:
            part: Part instance

        Returns:
            Total quantity across all stock items
        """
        try:
            from django.db.models import Sum
            from stock.models import StockItem

            result = StockItem.objects.filter(part=part).aggregate(
                total=Sum("quantity")
            )
            total = result.get("total") or 0
            return float(total)

        except Exception as e:
            logger.error(
                f"[Magento2StockSync] Error calculating quantity for Part {part.pk}: {e}"
            )
            return 0.0

    def _sync_to_magento(self, sku: str, quantity: float, event: str):
        """Sync stock quantity to Magento 2.

        Args:
            sku: Product SKU in Magento 2
            quantity: New quantity to set
            event: Event that triggered this sync
        """
        dry_run = self.get_setting("DRY_RUN", backup_value=False)

        if dry_run:
            logger.info(
                f"[Magento2StockSync] [DRY RUN] Would update SKU '{sku}' "
                f"to quantity {quantity} (event: {event})"
            )
            return

        try:
            client = self.get_magento_client()

            # Check if product exists in Magento 2
            product = client.get_product_by_sku(sku)
            if not product:
                logger.warning(
                    f"[Magento2StockSync] Product SKU '{sku}' not found in Magento 2"
                )
                return

            # Update the stock quantity
            client.update_product_stock(sku, quantity)
            logger.info(
                f"[Magento2StockSync] Successfully synced SKU '{sku}' "
                f"to Magento 2: quantity={quantity}"
            )

        except Magento2APIError as e:
            logger.error(f"[Magento2StockSync] API error syncing '{sku}': {e}")
        except ValueError as e:
            logger.error(f"[Magento2StockSync] Configuration error: {e}")
        except Exception as e:
            logger.error(
                f"[Magento2StockSync] Unexpected error syncing '{sku}': {e}",
                exc_info=True
            )
