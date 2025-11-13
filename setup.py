"""Setup configuration for InvenTree Magento 2 Stock Sync Plugin."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="inventree-magento2-sync",
    version="1.0.0",
    author="InvenTree Community",
    author_email="",
    description="InvenTree plugin to sync stock quantities to Magento 2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/inventree/inventree-magento2-sync",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "urllib3>=2.0.0",
    ],
    entry_points={
        "inventree_plugins": [
            "Magento2StockSyncPlugin = inventree_magento2_sync.plugin:Magento2StockSyncPlugin"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="inventree plugin magento2 stock inventory sync",
    include_package_data=True,
)
