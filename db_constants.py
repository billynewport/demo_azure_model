"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.
"""

# Model size. NUM_TEAMS=1 and NUM_STORES_PER_TEAM=75 creates 75 independent
# CDC ingestion streams over the same Azure SQL source tables.
NUM_TEAMS: int = 1
NUM_STORES_PER_TEAM: int = 75
CONSUMER_WORKSPACE_NAME: str = "AzureScaleConsumer"

# Provisioned Azure resource values for the AKS scale test.
AZURE_LOCATION_KEY: str = "Azure:USA/WestUS2"
AZURE_SOURCE_SQL_SERVER_HOST: str = "ds-scale-source-06030935-f006.database.windows.net"
AZURE_MERGE_SQL_SERVER_HOST: str = "ds-scale-merge-06030935-f006.database.windows.net"
AZURE_CQRS_SQL_SERVER_HOST: str = "ds-scale-cqrs-06030935-f006.database.windows.net"
AZURE_AIRFLOW_POSTGRES_HOST: str = "ds-scale-airflow-06030935-f006.postgres.database.azure.com"
AZURE_SQL_SERVER_PORT: int = 1433
AZURE_AIRFLOW_POSTGRES_PORT: int = 5432
AZURE_SOURCE_DBNAME: str = "customer_db"
AZURE_MERGE_DBNAME: str = "merge_db"
AZURE_CQRS_DBNAME: str = "cqrs_db"
AZURE_SQL_TRUST_SERVER_CERTIFICATE: bool = True

# Azure Blob bulk staging. AZURE_BULK_DATA_SOURCE_NAME must match the external
# data source name created in both Hyperscale databases.
AZURE_BULK_STORAGE_ACCOUNT: str = "dsscalebulk06030935f006"
AZURE_BULK_CONTAINER: str = "datasurface-bulk"
AZURE_BULK_PREFIX: str = "yellow/bulk-staging"
AZURE_BULK_DATA_SOURCE_NAME: str = "datasurface_bulk_ds"
AZURE_BULK_WRITER_CREDENTIAL: str = "azure-bulk-writer"

# Ingestion pod sizing for the Airflow/AKS concurrency test.
INGESTION_REQUEST_MEMORY: str = "512M"
INGESTION_LIMIT_MEMORY: str = "2G"
INGESTION_REQUEST_CPU: float = 0.25
INGESTION_LIMIT_CPU: float = 1.0
