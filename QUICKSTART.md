# Quick Start Guide

Get your InvenTree → Magento 2 stock sync up and running in 5 minutes.

## Prerequisites

- InvenTree instance running (Docker or bare metal)
- Magento 2 store with admin access
- Part names in InvenTree match SKUs in Magento 2

## Step 1: Install the Plugin

```bash
pip install git+https://github.com/inventree/inventree-magento2-sync.git
```

Or for local development:
```bash
cd /path/to/inventree-magento2-sync
pip install -e .
```

## Step 2: Restart InvenTree

```bash
# Docker
docker-compose restart

# Bare metal
sudo systemctl restart inventree
```

## Step 3: Activate Plugin in InvenTree

1. Log into InvenTree web interface as admin
2. Go to **Settings → Plugins**
3. Find "Magento 2 Stock Synchronization"
4. Click **Activate**

## Step 4: Get Magento 2 Access Token

1. Log into Magento 2 Admin Panel
2. Navigate to **System → Integrations**
3. Click **Add New Integration**
4. Fill in:
   - Name: `InvenTree Stock Sync`
   - Email: your-email@example.com
5. Click **API** tab
6. Grant permissions:
   - ✅ Catalog → Products (Read/Write)
   - ✅ Catalog → Inventory (Read/Write)
7. Click **Save**
8. Click **Activate**
9. **Copy the Access Token** (you'll need this in the next step)

## Step 5: Configure Plugin

1. In InvenTree, go to **Settings → Plugins → Magento 2 Stock Synchronization**
2. Configure:
   - **Magento 2 URL**: `https://yourstore.com` (no trailing slash)
   - **Access Token**: Paste the token from Step 4
   - **Enable Sync**: ✅ Check this box
   - **Dry Run Mode**: ✅ Check this initially for testing
3. Click **Save**

## Step 6: Test the Sync

### Test with Dry Run Mode Enabled

1. Find a Part in InvenTree whose name matches a Magento 2 SKU
2. Add or remove stock for that Part
3. Check InvenTree logs:

```bash
# Docker
docker-compose logs -f inventree

# Bare metal
tail -f /path/to/inventree/logs/inventree.log
```

You should see:
```
[DRY RUN] Would update Magento 2 SKU 'YOUR-SKU' to quantity 50.0
```

### Enable Real Syncing

1. Go back to plugin settings
2. Uncheck **Dry Run Mode**
3. Save
4. Make a stock change in InvenTree
5. Check Magento 2 - the quantity should update immediately!

## Verification Checklist

- ✅ Plugin shows as "Active" in InvenTree
- ✅ Dry run logs appear when stock changes
- ✅ No error messages in logs
- ✅ Magento 2 product quantity updates when dry run disabled
- ✅ Stock changes (add/remove/delete) all trigger sync

## Common Issues

### "Product with SKU 'XXX' not found in Magento 2"

**Problem**: Part name doesn't match Magento 2 SKU exactly.

**Solution**: Ensure InvenTree Part name = Magento 2 Product SKU (case-sensitive).

### "HTTP 401: Authentication failed"

**Problem**: Invalid or expired access token.

**Solution**: 
1. Go back to Magento 2 → System → Integrations
2. Click "Reauthorize" on your integration
3. Copy the new token
4. Update plugin settings in InvenTree

### No logs appearing

**Problem**: Sync might not be enabled or events not firing.

**Solution**:
1. Verify **Enable Sync** is checked
2. Verify **Sync on Create/Update/Delete** are checked
3. Check InvenTree general logs for errors

## Next Steps

Once working:

1. ✅ Disable **Dry Run Mode** for production use
2. ✅ Configure which events to sync (Create/Update/Delete)
3. ✅ Monitor logs for any errors
4. ✅ Test edge cases (deleting stock items, moving stock, etc.)

## Getting Help

- Plugin Issues: https://github.com/inventree/inventree-magento2-sync/issues
- InvenTree Docs: https://docs.inventree.org/
- Magento 2 API: https://developer.adobe.com/commerce/webapi/

## Advanced Configuration

See [README.md](README.md) for:
- SSL certificate verification settings
- Request timeout configuration
- Selective event syncing
- Troubleshooting guide
