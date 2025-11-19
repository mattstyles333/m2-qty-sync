# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-XX

### Added
- Comprehensive logging with `[Magento2StockSync]` prefix for easy filtering
- Visual separators in logs for better readability
- APICallMixin for better InvenTree API integration
- EVENTS.md documentation explaining InvenTree stock events
- Debug logging for event processing and settings state

### Changed
- **BREAKING**: Switched from Django model signals to InvenTree stock events
  - Now listens to: `stockitem.quantityupdated`, `stockitem.moved`, `stockitem.counted`, `stockitem.returnedtostock`, `stockitem.created_items`, etc.
  - Previously listened to: `stock_stockitem.created`, `stock_stockitem.saved`, `stock_stockitem.deleted`
- Removed `SYNC_ON_CREATE`, `SYNC_ON_UPDATE`, `SYNC_ON_DELETE` settings (all stock events now trigger sync)
- Updated README.md to reflect actual events being monitored

### Fixed
- Plugin not receiving any events (was listening for wrong event names)
- Package name mismatch between repo name and setup files
- Circular import in setup.py during installation

## [1.0.0] - 2025-01-XX

### Added
- Initial release
- Real-time stock synchronization from InvenTree to Magento 2
- Event-driven architecture using EventMixin
- Configurable settings via SettingsMixin
- Dry run mode for testing
- SSL verification support
- Comprehensive error handling and logging
- Support for Magento 2 REST API v1
- Automatic retry logic for failed API calls
- Total quantity calculation across all stock items
