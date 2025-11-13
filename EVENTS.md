# InvenTree Stock Events Reference

This plugin listens to **InvenTree's custom stock events** (not Django model signals).

## Events We Listen To

Based on InvenTree's `StockEvents` enumeration:

| Event Name | Description | Triggers Sync? |
|------------|-------------|----------------|
| `stockitem.quantityupdated` | Stock quantity changed (add/remove stock) | ✅ Yes |
| `stockitem.moved` | Stock item moved between locations | ✅ Yes |
| `stockitem.counted` | Stock counted/adjusted | ✅ Yes |
| `stockitem.split` | Stock item split into multiple items | ✅ Yes |
| `stockitem.assignedtocustomer` | Stock assigned to customer | ✅ Yes |
| `stockitem.returnedfromcustomer` | Stock returned from customer | ✅ Yes |
| `stockitem.installed` | Stock installed into assembly | ✅ Yes |

## How Events Work

1. **User action in InvenTree**: e.g., "Add 50 units to stock"
2. **InvenTree triggers event**: `stockitem.quantityupdated`
3. **Plugin receives event**: `wants_process_event()` is called
4. **Plugin checks if enabled**: Looks at `ENABLE_SYNC` setting
5. **Plugin processes**: Calculates total Part quantity
6. **Plugin syncs to Magento**: Updates product stock via API

## Event Data Structure

When `process_event()` is called, we receive:

```python
{
    'event': 'stockitem.quantityupdated',
    'model': 'StockItem',
    'id': 123,  # StockItem ID
    'instance': <StockItem object>  # The actual StockItem instance
}
```

## Common Confusion

❌ **NOT** Django model signals:
- `stock_stockitem.created`
- `stock_stockitem.saved`
- `stock_stockitem.deleted`

✅ **YES** InvenTree custom events:
- `stockitem.quantityupdated`
- `stockitem.moved`
- `stockitem.counted`

## Testing Events

To test if events are firing:

1. Enable the plugin with `DRY_RUN=True`
2. Watch the logs: `docker-compose logs -f inventree`
3. Make a stock change in InvenTree (add/remove stock)
4. Look for log messages: `[Magento2StockSync] Received event: 'stockitem.quantityupdated'`

## InvenTree Version Compatibility

These event names are from InvenTree's `stock/events.py` file. If your InvenTree version uses different event names, the plugin will need to be updated.

To check your InvenTree version's events, look at:
- `src/backend/InvenTree/stock/events.py` in the InvenTree source
- Or check the InvenTree documentation for your version
