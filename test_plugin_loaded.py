#!/usr/bin/env python3
"""Quick test to verify the plugin is installed and can be imported."""

try:
    from inventree_magento2_sync.plugin import Magento2StockSyncPlugin
    print("✓ Plugin can be imported")
    print(f"  Name: {Magento2StockSyncPlugin.NAME}")
    print(f"  Version: {Magento2StockSyncPlugin.VERSION}")
    print(f"  Title: {Magento2StockSyncPlugin.TITLE}")
    
    # Check settings
    print("\nPlugin Settings:")
    for key, config in Magento2StockSyncPlugin.SETTINGS.items():
        print(f"  - {config['name']}: {config.get('default', 'N/A')}")
    
    print("\n✓ Plugin structure looks good!")
    
except ImportError as e:
    print(f"✗ Failed to import plugin: {e}")
    exit(1)
