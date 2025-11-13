# InvenTree Magento 2 Stock Sync - Project Overview

## 🎯 What This Plugin Does

Automatically synchronizes stock quantities from InvenTree to Magento 2 in real-time whenever inventory changes occur in any way.

### The Problem It Solves

Without this plugin, you need to:
- Manually update Magento 2 when stock changes in InvenTree
- Write custom scripts to sync periodically
- Risk inventory mismatches between systems
- Lose sales due to inaccurate stock levels

### The Solution

This plugin automatically:
1. Detects ANY stock change in InvenTree (add, remove, create, delete)
2. Calculates the total available quantity for the affected Part
3. Updates the corresponding product in Magento 2 instantly
4. Logs the sync for auditing

## 📁 Complete File Listing

```
inventree-magento2-sync/
├── inventree_magento2_sync/          # Main plugin package
│   ├── __init__.py                   # Package initialization
│   ├── version.py                    # Version metadata (6 lines)
│   ├── magento_api.py                # Magento 2 API client (189 lines)
│   ├── plugin.py                     # Main plugin logic (303 lines)
│   └── tests/                        # Unit tests
│       ├── __init__.py
│       └── test_magento_api.py       # API client tests (169 lines)
│
├── README.md                         # Complete documentation
├── QUICKSTART.md                     # 5-minute setup guide
├── INSTALL.md                        # Installation & verification
├── SUMMARY.md                        # Technical implementation details
├── PROJECT_OVERVIEW.md              # This file
│
├── setup.py                          # Package setup (classic format)
├── pyproject.toml                    # Modern Python packaging
├── requirements.txt                  # Python dependencies
├── MANIFEST.in                       # Package manifest
├── LICENSE                           # MIT License
└── .gitignore                        # Git ignore rules
```

**Total:** 671 lines of Python code + comprehensive documentation

## 🔧 Core Components

### 1. Magento 2 API Client (`magento_api.py`)

**Purpose:** Handle all communication with Magento 2 REST API

**Features:**
- Bearer token authentication
- Automatic retry with exponential backoff
- Connection pooling for performance
- SSL certificate verification (optional)
- Comprehensive error handling
- Timeout configuration

**Key Methods:**
```python
get_product_by_sku(sku)          # Check if product exists
update_product_stock(sku, qty)   # Update product quantity
test_connection()                # Verify API credentials
```

### 2. Event Handler Plugin (`plugin.py`)

**Purpose:** Listen for stock changes and trigger Magento 2 sync

**Mixins Used:**
- `EventMixin` - Listen for database events
- `SettingsMixin` - User-configurable settings

**Events Monitored:**
- `stock_stockitem.created` - New stock items
- `stock_stockitem.saved` - Updated stock items
- `stock_stockitem.deleted` - Deleted stock items

**Key Methods:**
```python
wants_process_event(event)       # Filter which events to handle
process_event(event, **kwargs)   # Process the event
_calculate_total_quantity(part)  # Sum all stock for a Part
_sync_to_magento(sku, quantity)  # Update Magento 2
```

### 3. Configuration System

**9 Configurable Settings:**

| Setting | Type | Purpose |
|---------|------|---------|
| MAGENTO_URL | string | Your Magento 2 store URL |
| ACCESS_TOKEN | string | API authentication token (protected) |
| ENABLE_SYNC | bool | Master on/off switch |
| DRY_RUN | bool | Test mode without actual updates |
| VERIFY_SSL | bool | SSL certificate verification |
| TIMEOUT | int | API request timeout (seconds) |
| SYNC_ON_CREATE | bool | Sync when stock created |
| SYNC_ON_UPDATE | bool | Sync when stock updated |
| SYNC_ON_DELETE | bool | Sync when stock deleted |

## 🔄 How It Works - Step by Step

### Example: Receiving New Inventory

**Scenario:** You receive 50 units of WIDGET-123

1. **InvenTree Action:**
   - User creates new StockItem for Part "WIDGET-123"
   - Quantity: 50 units
   - Location: Warehouse A

2. **Event Triggered:**
   ```
   Event: stock_stockitem.created
   StockItem ID: 789
   Part: WIDGET-123
   ```

3. **Plugin Processing:**
   ```python
   # Plugin receives event
   wants_process_event('stock_stockitem.created')  # Returns True
   
   # Extract Part from StockItem
   part = get_part_from_event(instance)  # Part: WIDGET-123
   
   # Calculate total quantity (all stock items for this Part)
   total_qty = calculate_total_quantity(part)  # Result: 50
   
   # Sync to Magento 2
   magento_client.update_product_stock('WIDGET-123', 50)
   ```

4. **Magento 2 API Call:**
   ```http
   PUT /rest/V1/products/WIDGET-123/stockItems/1
   {
     "stockItem": {
       "qty": 50,
       "is_in_stock": true
     }
   }
   ```

5. **Result:**
   - Magento 2 product WIDGET-123 now shows 50 units in stock
   - Customers can see updated availability
   - Log entry created: "Successfully synced SKU 'WIDGET-123' to Magento 2: quantity=50.0"

### Example: Multiple Stock Locations

**Scenario:** Same Part in multiple locations

**InvenTree:**
- Part: WIDGET-123
- StockItem #1: 50 units (Warehouse A)
- StockItem #2: 30 units (Warehouse B)
- **Total: 80 units**

**Magento 2:**
- SKU: WIDGET-123
- Quantity: **80** (automatically calculated)

**When StockItem #2 is deleted:**
1. Event: `stock_stockitem.deleted`
2. Plugin calculates new total: 50 units (only StockItem #1 remains)
3. Magento 2 updated to: 50 units

## 🛡️ Error Handling

### Network Errors
```python
try:
    client.update_product_stock(sku, qty)
except Magento2APIError as e:
    logger.error(f"Failed to sync: {e}")
    # Plugin continues, doesn't crash InvenTree
```

### Missing Configuration
```python
if not magento_url or not access_token:
    logger.error("Magento 2 credentials not configured")
    return  # Skip sync gracefully
```

### Product Not Found
```python
product = client.get_product_by_sku(sku)
if not product:
    logger.warning(f"Product '{sku}' not found in Magento 2")
    return  # Skip this product
```

## 📊 Logging Examples

### Successful Sync
```
[INFO] Processing event 'stock_stockitem.created' for StockItem ID 123
[INFO] Part 'WIDGET-123' (ID 45) total quantity: 50.0
[INFO] Successfully updated Magento 2 stock for SKU 'WIDGET-123': qty=50.0, in_stock=True
[INFO] Successfully synced SKU 'WIDGET-123' to Magento 2: quantity=50.0
```

### Dry Run Mode
```
[INFO] Processing event 'stock_stockitem.saved' for StockItem ID 124
[INFO] Part 'WIDGET-123' (ID 45) total quantity: 60.0
[INFO] [DRY RUN] Would update Magento 2 SKU 'WIDGET-123' to quantity 60.0 (triggered by stock_stockitem.saved)
```

### Error Handling
```
[WARNING] Product with SKU 'NONEXISTENT-SKU' not found in Magento 2, skipping sync
[ERROR] Failed to sync SKU 'WIDGET-123' to Magento 2: HTTP 401: Authentication failed
[ERROR] Magento 2 API connection error: Connection refused
```

## 🚀 Installation & Setup (Summary)

### 1. Install
```bash
pip install git+https://github.com/inventree/inventree-magento2-sync.git
```

### 2. Restart InvenTree
```bash
docker-compose restart  # or systemctl restart inventree
```

### 3. Enable in UI
Settings → Plugins → Magento 2 Stock Synchronization → Activate

### 4. Configure
- Magento 2 URL: `https://yourstore.com`
- Access Token: (from Magento 2 Integration)
- Enable Sync: ✓
- Dry Run Mode: ✓ (for testing)

### 5. Test
- Make a stock change
- Check logs for "[DRY RUN]" message
- Verify no errors

### 6. Go Live
- Uncheck Dry Run Mode
- Make stock change
- Verify Magento 2 updates

## 📖 Documentation Guide

### For End Users
1. Start with **QUICKSTART.md** - Get running in 5 minutes
2. Read **README.md** - Complete feature documentation
3. Refer to **INSTALL.md** - Troubleshooting installation

### For Developers
1. Read **SUMMARY.md** - Technical implementation details
2. Review code in `plugin.py` and `magento_api.py`
3. Check `tests/test_magento_api.py` for usage examples

### For System Administrators
1. Follow **INSTALL.md** - Installation verification
2. Monitor logs as shown in **README.md** troubleshooting section
3. Configure settings based on **README.md** configuration table

## 🧪 Testing

### Unit Tests
```bash
pytest inventree_magento2_sync/tests/
```

**Coverage:**
- API client initialization
- Product lookup (success/404)
- Stock updates (success/failure)
- Error handling (network, auth, timeout)
- Connection testing

### Manual Testing
1. Enable dry run mode
2. Create/update/delete stock items
3. Verify logs show correct calculations
4. Disable dry run
5. Verify Magento 2 updates

## 🔐 Security Features

- **Protected Settings:** Access token marked as protected (hidden in UI)
- **SSL Verification:** Optional SSL certificate verification
- **No Plain Text Secrets:** Credentials stored in InvenTree's secure settings
- **Audit Trail:** All sync operations logged
- **Read-Only Product Access:** Only updates stock, doesn't modify products

## 🎓 Key Concepts

### Part Name = Magento 2 SKU
This is the critical mapping. Ensure:
```
InvenTree Part Name: WIDGET-123
Magento 2 Product SKU: WIDGET-123
```

### Total Quantity Sync
Plugin ALWAYS syncs the TOTAL quantity across all stock items:
```
StockItem #1: 30 units
StockItem #2: 20 units
StockItem #3: 10 units
-----------------------------
Magento 2 Qty: 60 units (total)
```

### Event-Driven Architecture
No polling, no scheduled tasks. Updates happen INSTANTLY when stock changes.

## 📦 Dependencies

**Runtime:**
- `requests>=2.31.0` - HTTP client
- `urllib3>=2.0.0` - Connection pooling

**InvenTree Provides:**
- Django (models, database)
- Plugin framework (EventMixin, SettingsMixin)
- Logging infrastructure

## 🌟 Next Steps

### After Installation
1. ✅ Test with dry run mode
2. ✅ Verify a few products sync correctly
3. ✅ Enable live sync
4. ✅ Monitor logs for first few hours
5. ✅ Set up alerting for errors (optional)

### Future Enhancements
- Batch sync for initial data load
- Bidirectional sync (M2 → InvenTree)
- Multi-warehouse mapping
- Custom field mapping
- Sync status dashboard
- Historical sync logs UI

## 🆘 Getting Help

1. **Documentation:** README.md has extensive troubleshooting
2. **Logs:** Check InvenTree logs for detailed error messages
3. **Dry Run:** Use dry run mode to diagnose issues
4. **GitHub Issues:** Report bugs or request features
5. **InvenTree Community:** Ask in InvenTree forums/Discord

## 📝 License

MIT License - Free to use, modify, and distribute.

## 👥 Contributing

Contributions welcome! Areas for improvement:
- Additional test coverage
- Performance optimizations
- UI enhancements
- Documentation improvements
- Bug fixes

---

**Plugin Version:** 1.0.0  
**Last Updated:** 2025-01-12  
**Status:** Production Ready
