"""InvenTree plugin for synchronizing stock to Magento 2."""

import logging

from plugin import InvenTreePlugin
from plugin.mixins import EventMixin, SettingsMixin

from .magento_api import Magento2APIError, Magento2Client
from .version import PLUGIN_NAME, PLUGIN_SLUG, PLUGIN_TITLE, PLUGIN_VERSION

logger = logging.getLogger("inventree")


class Magento2StockSyncPlugin(EventMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to synchronize InvenTree stock quantities to Magento 2.

    This plugin listens for stock item changes (create, update, delete) and
    automatically updates the corresponding product quantity in Magento 2.

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
    WEBSITE = "https://github.com/inventree/inventree-magento2-sync"
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
        "SYNC_ON_CREATE": {
            "name": "Sync on Create",
            "description": "Sync to Magento 2 when new stock items are created",
            "default": True,
            "validator": bool,
        },
        "SYNC_ON_UPDATE": {
            "name": "Sync on Update",
            "description": "Sync to Magento 2 when stock items are updated",
            "default": True,
            "validator": bool,
        },
        "SYNC_ON_DELETE": {
            "name": "Sync on Delete",
            "description": "Sync to Magento 2 when stock items are deleted",
            "default": True,
            "validator": bool,
        },
    }

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self._client = None
        logger.info("=" * 60)
        logger.info(f"Magento2StockSyncPlugin v{PLUGIN_VERSION} initialized")
        logger.info("=" * 60)

    def get_magento_client(self) -> Magento2Client:
        """Get or create a Magento 2 API client.

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

        # Create new client with current settings
        return Magento2Client(
            base_url=magento_url,
            access_token=access_token,
            timeout=self.get_setting("TIMEOUT", 30),
            verify_ssl=self.get_setting("VERIFY_SSL", True),
        )

    def wants_process_event(self, event: str) -> bool:
        """Determine if this event should be processed.

        Only process stock item creation, update, and deletion events.

        Args:
            event: Event name

        Returns:
            True if the event should be processed
        """
        # Log ALL events to help diagnose
        logger.info(f"[Magento2StockSync] Received event: '{event}'")
        
        # Check if sync is enabled
        sync_enabled = self.get_setting("ENABLE_SYNC", False)
        logger.info(f"[Magento2StockSync] ENABLE_SYNC setting: {sync_enabled}")
        
        if not sync_enabled:
            logger.warning(f"[Magento2StockSync] Ignoring event '{event}' - sync is DISABLED in settings")
            return False

        # Check which events to process based on settings
        sync_on_create = self.get_setting("SYNC_ON_CREATE", True)
        sync_on_update = self.get_setting("SYNC_ON_UPDATE", True)
        sync_on_delete = self.get_setting("SYNC_ON_DELETE", True)
        
        logger.info(
            f"[Magento2StockSync] Event settings: "
            f"SYNC_ON_CREATE={sync_on_create}, "
            f"SYNC_ON_UPDATE={sync_on_update}, "
            f"SYNC_ON_DELETE={sync_on_delete}"
        )
        
        event_map = {
            "stock_stockitem.created": sync_on_create,
            "stock_stockitem.saved": sync_on_update,
            "stock_stockitem.deleted": sync_on_delete,
        }

        should_process = event_map.get(event, False)
        
        logger.info(
            f"[Magento2StockSync] Event '{event}' - "
            f"will_process={should_process}"
        )
        
        return should_process

    def process_event(self, event: str, *args, **kwargs):
        """Process a stock change event and sync to Magento 2.

        Args:
            event: Event name
            *args: Positional arguments from event
            **kwargs: Keyword arguments from event (includes 'model', 'id', 'instance')
        """
        logger.info("=" * 60)
        logger.info(f"[Magento2StockSync] PROCESS_EVENT CALLED")
        logger.info(f"[Magento2StockSync] Event: '{event}'")
        logger.info(f"[Magento2StockSync] Args: {args}")
        logger.info(f"[Magento2StockSync] Kwargs keys: {list(kwargs.keys())}")
        logger.info("=" * 60)
        
        try:
            # Extract event data
            model = kwargs.get("model")
            stock_item_id = kwargs.get("id")
            instance = kwargs.get("instance")

            logger.info(
                f"[Magento2StockSync] Processing event '{event}' for StockItem ID {stock_item_id}"
            )

            # Get the Part associated with this StockItem
            part = self._get_part_from_event(event, instance, stock_item_id, **kwargs)

            if not part:
                logger.warning(
                    f"[Magento2StockSync] Could not determine Part for StockItem ID {stock_item_id}, skipping sync"
                )
                return

            # Use Part name as Magento 2 SKU
            sku = part.name

            if not sku:
                logger.warning(
                    f"[Magento2StockSync] Part ID {part.pk} has no name, cannot sync to Magento 2"
                )
                return

            # Calculate total available quantity for this Part
            total_quantity = self._calculate_total_quantity(part)

            logger.info(
                f"[Magento2StockSync] Part '{sku}' (ID {part.pk}) total quantity: {total_quantity}"
            )

            # Sync to Magento 2
            self._sync_to_magento(sku, total_quantity, event)

        except Exception as e:
            logger.error(f"[Magento2StockSync] Error processing event '{event}': {str(e)}", exc_info=True)

    def _get_part_from_event(
        self, event: str, instance, stock_item_id: int, **kwargs
    ):
        """Extract the Part from the event data.

        Args:
            event: Event name
            instance: StockItem instance (if available)
            stock_item_id: StockItem ID
            **kwargs: Additional event data

        Returns:
            Part instance or None
        """
        # For delete events, the instance is still available in memory
        # For create/update events, we can query the database
        if instance and hasattr(instance, "part"):
            return instance.part

        # Fallback: try to import and query the StockItem
        # (works for create/update, but not for delete)
        if event != "stock_stockitem.deleted":
            try:
                from stock.models import StockItem

                stock_item = StockItem.objects.get(pk=stock_item_id)
                return stock_item.part
            except Exception as e:
                logger.error(
                    f"Could not fetch StockItem ID {stock_item_id}: {str(e)}"
                )

        return None

    def _calculate_total_quantity(self, part) -> float:
        """Calculate total available quantity for a Part.

        Sums up all stock items for the given part.

        Args:
            part: Part instance

        Returns:
            Total quantity across all stock items
        """
        try:
            from django.db.models import Sum
            from stock.models import StockItem

            # Get all stock items for this part and sum their quantities
            result = StockItem.objects.filter(part=part).aggregate(
                total=Sum("quantity")
            )

            total = result.get("total") or 0
            return float(total)

        except Exception as e:
            logger.error(
                f"Error calculating total quantity for Part ID {part.pk}: {str(e)}"
            )
            return 0

    def _sync_to_magento(self, sku: str, quantity: float, event: str):
        """Sync stock quantity to Magento 2.

        Args:
            sku: Product SKU in Magento 2
            quantity: New quantity to set
            event: Event that triggered this sync
        """
        dry_run = self.get_setting("DRY_RUN", False)
        
        logger.info(f"[Magento2StockSync] Syncing to Magento: SKU='{sku}', qty={quantity}, dry_run={dry_run}")

        if dry_run:
            logger.warning(
                f"[Magento2StockSync] [DRY RUN] Would update Magento 2 SKU '{sku}' to quantity {quantity} "
                f"(triggered by {event})"
            )
            return

        try:
            client = self.get_magento_client()

            # Check if product exists in Magento 2
            product = client.get_product_by_sku(sku)

            if not product:
                logger.warning(
                    f"[Magento2StockSync] Product with SKU '{sku}' not found in Magento 2, skipping sync"
                )
                return

            # Update the stock quantity
            logger.info(f"[Magento2StockSync] Updating Magento 2 stock for SKU '{sku}' to {quantity}")
            client.update_product_stock(sku, quantity)

            logger.info(
                f"[Magento2StockSync] ✓ Successfully synced SKU '{sku}' to Magento 2: quantity={quantity}"
            )

        except Magento2APIError as e:
            logger.error(f"[Magento2StockSync] Failed to sync SKU '{sku}' to Magento 2: {str(e)}")
        except ValueError as e:
            logger.error(f"[Magento2StockSync] Configuration error: {str(e)}")
        except Exception as e:
            logger.error(
                f"[Magento2StockSync] Unexpected error syncing SKU '{sku}' to Magento 2: {str(e)}",
                exc_info=True,
            )
