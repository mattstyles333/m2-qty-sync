# InvenTree Magento 2 Stock Sync Plugin

Automatically synchronize stock quantities from InvenTree to Magento 2 in real-time.

## Features

- **Automatic Sync**: Listens for any stock changes in InvenTree and updates Magento 2 instantly
- **Event-Driven**: Uses InvenTree's event system to capture:
  - New stock items created
  - Stock quantities updated (add/remove/count)
  - Stock items deleted
- **Smart Mapping**: Maps InvenTree Part Name → Magento 2 Product SKU
- **Total Quantity**: Always syncs the total available quantity across all stock items
- **Configurable**: Enable/disable sync per event type (create/update/delete)
- **Dry Run Mode**: Test the sync without actually updating Magento 2
- **Error Handling**: Comprehensive logging and error handling
- **SSL Support**: Optional SSL certificate verification

## How It Works

1. A stock change occurs in InvenTree (e.g., receiving inventory, adjusting stock, deleting a stock item)
2. Plugin captures the event and identifies the affected Part
3. Plugin calculates the total available quantity for that Part
4. Plugin updates the corresponding product in Magento 2 using the Part name as SKU

### Example Flow

**InvenTree:**
- Part Name: `WIDGET-123`
- StockItem #1: 50 units in Warehouse A
- StockItem #2: 30 units in Warehouse B
- **Total: 80 units**

**Magento 2:**
- Product SKU: `WIDGET-123`
- Quantity: **80 units** (automatically updated)

If StockItem #2 is deleted, Magento 2 is instantly updated to show 50 units.

## Installation

### Method 1: Install from PyPI (when published)

```bash
pip install inventree-magento2-sync
```

### Method 2: Install from Git Repository

```bash
pip install git+https://github.com/inventree/inventree-magento2-sync.git
```

### Method 3: Install from Local Directory

```bash
cd /path/to/inventree-magento2-sync
pip install -e .
```

### Enable the Plugin

1. Restart your InvenTree server
2. Navigate to **Settings → Plugins** in the InvenTree web interface
3. Find "Magento 2 Stock Synchronization" in the plugin list
4. Click **Activate** to enable the plugin

## Configuration

After enabling the plugin, configure it via **Settings → Plugins → Magento 2 Stock Synchronization**:

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| **Magento 2 URL** | Base URL of your Magento 2 store | `https://example.com` |
| **Access Token** | Integration access token from Magento 2 | `abc123def456...` |

### Optional Settings

| Setting | Default | Description |
|---------|---------|-------------|
| **Enable Sync** | `False` | Master switch to enable/disable all syncing |
| **Dry Run Mode** | `False` | Log actions without updating Magento 2 |
| **Verify SSL** | `True` | Verify SSL certificates |
| **Request Timeout** | `30` | API request timeout in seconds |
| **Sync on Create** | `True` | Sync when new stock items are created |
| **Sync on Update** | `True` | Sync when stock items are updated |
| **Sync on Delete** | `True` | Sync when stock items are deleted |

## Magento 2 Setup

### Create Integration Access Token

1. Log into Magento 2 Admin Panel
2. Navigate to **System → Integrations**
3. Click **Add New Integration**
4. Fill in the details:
   - **Name**: InvenTree Stock Sync
   - **Email**: your-email@example.com
5. Go to **API** tab and select these permissions:
   - **Catalog → Products** (Read/Write)
   - **Catalog → Inventory** (Read/Write)
6. Click **Save**
7. Click **Activate** and copy the **Access Token**
8. Paste the token into the plugin settings in InvenTree

## Part Name Mapping

**Important**: The plugin uses the InvenTree **Part Name** as the Magento 2 **Product SKU**.

Make sure your Part names in InvenTree match the SKUs in Magento 2:

✅ **Correct Setup:**
- InvenTree Part Name: `WIDGET-123`
- Magento 2 Product SKU: `WIDGET-123`

❌ **Won't Sync:**
- InvenTree Part Name: `Blue Widget`
- Magento 2 Product SKU: `WIDGET-123`

## Testing

### Test the Connection

1. Enable **Dry Run Mode** in plugin settings
2. Enable **Enable Sync**
3. Make a stock change in InvenTree
4. Check the InvenTree logs for sync messages:

```bash
tail -f /path/to/inventree/logs/inventree.log
```

You should see:
```
[DRY RUN] Would update Magento 2 SKU 'WIDGET-123' to quantity 80.0
```

5. Once confirmed, disable **Dry Run Mode** to enable actual syncing

### Manual Testing

Create a simple stock change and verify:

1. In InvenTree, find a Part with matching Magento 2 SKU
2. Add or remove stock
3. Check Magento 2 to confirm quantity updated
4. Check InvenTree logs for success message

## Troubleshooting

### Plugin Not Syncing

1. Check that **Enable Sync** is enabled
2. Check that the appropriate event sync settings are enabled (Create/Update/Delete)
3. Verify Magento 2 credentials are correct
4. Check InvenTree logs for error messages

### Product Not Found in Magento 2

```
Product with SKU 'WIDGET-123' not found in Magento 2, skipping sync
```

**Solution**: Ensure the InvenTree Part name exactly matches the Magento 2 product SKU.

### Authentication Failed

```
HTTP 401: Authentication failed
```

**Solution**: 
- Verify the Access Token is correct
- Ensure the Integration is activated in Magento 2
- Check that API permissions include Catalog and Inventory

### SSL Certificate Error

```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution**: 
- If using self-signed certificates, disable **Verify SSL** in plugin settings
- Or install proper SSL certificates on your Magento 2 server

### Connection Timeout

```
Request timeout after 30s
```

**Solution**: Increase **Request Timeout** in plugin settings (e.g., 60 seconds)

## Development

### Project Structure

```
inventree-magento2-sync/
├── inventree_magento2_sync/
│   ├── __init__.py
│   ├── plugin.py          # Main plugin class with event handling
│   ├── magento_api.py     # Magento 2 API client
│   └── version.py         # Version information
├── tests/
│   ├── __init__.py
│   └── test_magento_api.py
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── LICENSE
```

### Running Tests

```bash
pytest tests/
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/inventree/inventree-magento2-sync.git
cd inventree-magento2-sync

# Install in editable mode
pip install -e .

# Restart InvenTree
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: https://github.com/inventree/inventree-magento2-sync/issues
- **InvenTree Documentation**: https://docs.inventree.org/
- **Magento 2 API Docs**: https://developer.adobe.com/commerce/webapi/

## Changelog

### 1.0.0 (2025-01-12)

- Initial release
- Event-driven stock synchronization
- Support for create, update, and delete events
- Configurable sync options
- Dry run mode
- Comprehensive error handling and logging
