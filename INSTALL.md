# Installation & Verification Guide

## Installation Methods

### Method 1: Install from Git (Recommended for Testing)

```bash
pip install git+https://github.com/inventree/inventree-magento2-sync.git
```

### Method 2: Install from Local Directory

```bash
# Clone or download the repository
cd /path/to/inventree-magento2-sync

# Install in development mode (for testing/development)
pip install -e .

# Or install normally
pip install .
```

### Method 3: Install from PyPI (Once Published)

```bash
pip install inventree-magento2-sync
```

## Verification Steps

### 1. Verify Installation

```bash
# Check if package is installed
pip list | grep inventree-magento2-sync

# Should output:
# inventree-magento2-sync  1.0.0
```

### 2. Restart InvenTree

**Docker:**
```bash
docker-compose restart
```

**Bare Metal:**
```bash
sudo systemctl restart inventree
# or
invoke restart
```

### 3. Check Plugin Discovery

After restart, check InvenTree logs for plugin discovery:

```bash
# Docker
docker-compose logs inventree | grep -i "Magento2StockSync"

# Bare Metal
tail -f /path/to/inventree/logs/inventree.log | grep -i "Magento2StockSync"
```

You should see:
```
Discovered plugin: Magento2StockSyncPlugin
```

### 4. Enable Plugin in InvenTree UI

1. Open InvenTree web interface
2. Log in as administrator
3. Navigate to **Settings** (gear icon) → **Plugins**
4. Find "Magento 2 Stock Synchronization" in the plugin list
5. If status shows "Inactive", click the plugin name
6. Click **Activate** button
7. Verify status changes to "Active"

### 5. Access Plugin Settings

1. While in **Settings → Plugins**
2. Click on "Magento 2 Stock Synchronization"
3. You should see the settings page with 9 configuration options:
   - Magento 2 URL
   - Access Token
   - Enable Sync
   - Dry Run Mode
   - Verify SSL
   - Request Timeout
   - Sync on Create
   - Sync on Update
   - Sync on Delete

### 6. Configure Magento 2 Integration

See [QUICKSTART.md](QUICKSTART.md) for detailed Magento 2 setup.

Quick steps:
1. In Magento 2 Admin: **System → Integrations**
2. Create new integration with Catalog/Inventory permissions
3. Activate and copy Access Token
4. In InvenTree plugin settings, paste:
   - **Magento 2 URL**: `https://yourstore.com`
   - **Access Token**: (paste token)
   - **Enable Sync**: ☑️ Check
   - **Dry Run Mode**: ☑️ Check (for testing)
5. Click **Save**

### 7. Test Connection (Dry Run)

1. Ensure **Dry Run Mode** is enabled
2. In InvenTree, find a Part whose name matches a Magento 2 SKU
3. Add stock to that Part (e.g., +10 units)
4. Watch the logs:

```bash
# Docker
docker-compose logs -f inventree

# Bare Metal
tail -f /path/to/inventree/logs/inventree.log
```

**Expected output:**
```
Processing event 'stock_stockitem.created' for StockItem ID 123
Part 'WIDGET-123' (ID 45) total quantity: 50.0
[DRY RUN] Would update Magento 2 SKU 'WIDGET-123' to quantity 50.0 (triggered by stock_stockitem.created)
```

### 8. Enable Live Sync

Once dry run tests pass:

1. Go back to plugin settings
2. Uncheck **Dry Run Mode**
3. Click **Save**
4. Make another stock change
5. Verify in Magento 2 that the quantity updated

**Expected log:**
```
Processing event 'stock_stockitem.saved' for StockItem ID 124
Part 'WIDGET-123' (ID 45) total quantity: 60.0
Successfully updated Magento 2 stock for SKU 'WIDGET-123': qty=60.0, in_stock=True
Successfully synced SKU 'WIDGET-123' to Magento 2: quantity=60.0
```

## Troubleshooting Installation

### Plugin Not Appearing

**Problem**: Plugin doesn't show in Settings → Plugins

**Solutions**:
```bash
# Verify package is installed
pip list | grep inventree-magento2-sync

# Check Python path
python -c "import inventree_magento2_sync; print(inventree_magento2_sync.__file__)"

# Restart InvenTree
docker-compose restart  # or systemctl restart inventree
```

### Import Errors

**Problem**: Errors about missing modules when InvenTree starts

**Solution**:
```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Or reinstall the package
pip install --force-reinstall inventree-magento2-sync
```

### Plugin Activation Fails

**Problem**: Error when clicking Activate

**Check**:
1. InvenTree logs for specific error
2. Ensure InvenTree version is compatible
3. Verify no conflicting plugins

### Settings Not Saving

**Problem**: Plugin settings revert after save

**Solution**:
1. Check file permissions on InvenTree data directory
2. Verify database is writable
3. Check InvenTree logs for database errors

## Uninstallation

### Disable Plugin First

1. In InvenTree UI: Settings → Plugins
2. Click on "Magento 2 Stock Synchronization"
3. Click **Deactivate**
4. Wait for confirmation

### Uninstall Package

```bash
pip uninstall inventree-magento2-sync
```

### Restart InvenTree

```bash
docker-compose restart
# or
systemctl restart inventree
```

## Development Installation

For plugin development:

```bash
# Clone the repository
git clone https://github.com/inventree/inventree-magento2-sync.git
cd inventree-magento2-sync

# Install in editable mode
pip install -e .

# Make changes to the code
# InvenTree will auto-reload on code changes (in development mode)
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest inventree_magento2_sync/tests/

# Run with coverage
pytest --cov=inventree_magento2_sync inventree_magento2_sync/tests/
```

## Environment-Specific Notes

### Docker Installation

If running InvenTree in Docker, you may need to install the plugin inside the container:

```bash
# Enter the container
docker-compose exec inventree bash

# Install plugin
pip install git+https://github.com/inventree/inventree-magento2-sync.git

# Exit and restart
exit
docker-compose restart
```

Or add to your `requirements.txt` or `Dockerfile`.

### Virtual Environment

If InvenTree runs in a virtual environment:

```bash
# Activate the venv first
source /path/to/inventree/venv/bin/activate

# Then install
pip install inventree-magento2-sync

# Restart InvenTree
systemctl restart inventree
```

## Next Steps

Once installed and verified:

1. ✅ Read [QUICKSTART.md](QUICKSTART.md) for configuration
2. ✅ Read [README.md](README.md) for full documentation
3. ✅ Test with dry run mode first
4. ✅ Enable live sync
5. ✅ Monitor logs for errors
6. ✅ Set up monitoring/alerting for production use

## Support

If you encounter issues:

1. Check the logs (InvenTree and Magento 2)
2. Verify configuration settings
3. Test with dry run mode
4. Consult troubleshooting guide in README.md
5. Open an issue: https://github.com/inventree/inventree-magento2-sync/issues
