"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.

Azure AKS runtime environment configuration for the concurrent-ingestion scale
model. Replace the literal host/database/storage values after Azure resources
are provisioned, then commit the updated model.
"""

from datasurface.containers import AzureObjectContainer, AzureSQLHyperscaleDatabase, DataContainerParams, HostPortPair
from datasurface.documentation import PlainTextDocumentation
from datasurface.dsl import (
    ConsumerReplicaGroup,
    DataMilestoningStrategy,
    Ecosystem,
    PSPDeclaration,
    ProductionStatus,
    RuntimeEnvironment,
    StorageRequirement,
)
from datasurface.keys import LocationKey
from datasurface.repos import GitHubRepository, ReleaseType, VersionPatternReleaseSelector, VersionPatterns
from datasurface.security import Credential, CredentialType
from datasurface.triggers import CronTrigger
from datasurface.yellow import (
    BulkObjectStorageBinding,
    GitCacheConfig,
    K8sIngestionHint,
    K8sResourceLimits,
    YellowAzureExternalAirflow3AndMergeDatabase,
    YellowDataPlatform,
    YellowPlatformServiceProvider,
)
from datasurface.platforms.yellow import K8sCQRSHint

from db_constants import (
    AZURE_AIRFLOW_POSTGRES_HOST,
    AZURE_AIRFLOW_POSTGRES_PORT,
    AZURE_BULK_CONTAINER,
    AZURE_BULK_DATA_SOURCE_NAME,
    AZURE_BULK_PREFIX,
    AZURE_BULK_STORAGE_ACCOUNT,
    AZURE_BULK_WRITER_CREDENTIAL,
    AZURE_CQRS_DBNAME,
    AZURE_CQRS_SQL_SERVER_HOST,
    AZURE_LOCATION_KEY,
    AZURE_MERGE_DBNAME,
    AZURE_MERGE_SQL_SERVER_HOST,
    AZURE_SQL_SERVER_PORT,
    AZURE_SQL_TRUST_SERVER_CERTIFICATE,
    CONSUMER_WORKSPACE_NAME,
    INGESTION_LIMIT_CPU,
    INGESTION_LIMIT_MEMORY,
    INGESTION_REQUEST_CPU,
    INGESTION_REQUEST_MEMORY,
    NUM_STORES_PER_TEAM,
    NUM_TEAMS,
)


KUB_NAME_SPACE: str = "ds-scale"
AIRFLOW_HOST: str = AZURE_AIRFLOW_POSTGRES_HOST
AIRFLOW_PORT: int = AZURE_AIRFLOW_POSTGRES_PORT
AIRFLOW_SERVICE_ACCOUNT: str = "airflow-worker"
DATASURFACE_VERSION: str = "1.4.47"
CRG_NAME: str = "AzureHyperscaleCQRS"
CQRS_CONTAINER_NAME: str = "AzureHyperscale_CQRS_DB"
CQRS_MAX_WORKERS: int = 8
CQRS_REMOTE_FORENSIC_MAX_COALESCE_RANGE: int = 200
CQRS_REQUEST_CPU: float = 0.25
CQRS_LIMIT_CPU: float = 1.0
CQRS_REQUEST_MEMORY: str = "2G"
CQRS_LIMIT_MEMORY: str = "4G"
CQRS_STAGING_CHUNK_SIZE: int = 500000
CQRS_BULK_STAGING_ROWS_PER_PART: int = 250000


def _location() -> LocationKey:
    return LocationKey(AZURE_LOCATION_KEY)


def _azure_bulk_binding() -> BulkObjectStorageBinding:
    return BulkObjectStorageBinding(
        AzureObjectContainer(
            AZURE_BULK_DATA_SOURCE_NAME,
            {_location()},
            storageAccountName=AZURE_BULK_STORAGE_ACCOUNT,
            containerName=AZURE_BULK_CONTAINER,
            prefix=AZURE_BULK_PREFIX,
        ),
        writerCredential=Credential(AZURE_BULK_WRITER_CREDENTIAL, CredentialType.USER_PASSWORD),
    )


def _ingestion_hints() -> list[K8sIngestionHint]:
    resources = K8sResourceLimits(
        StorageRequirement(INGESTION_REQUEST_MEMORY),
        StorageRequirement(INGESTION_LIMIT_MEMORY),
        INGESTION_REQUEST_CPU,
        INGESTION_LIMIT_CPU,
    )
    return [
        K8sIngestionHint(
            resourceLimits=resources,
            kv={
                "bulkStagingMode": "force",
                "bulkStagingRowsPerPart": 50000,
                "bulkStagingMinRows": 1,
                "bulkUploadMaxSinglePutMiB": 4,
                "bulkUploadChunkMiB": 4,
                "bulkUploadMaxConcurrency": 2,
            },
        )
    ]


def _cqrs_hint() -> K8sCQRSHint:
    return K8sCQRSHint(
        CRG_NAME,
        K8sResourceLimits(
            StorageRequirement(CQRS_REQUEST_MEMORY),
            StorageRequirement(CQRS_LIMIT_MEMORY),
            CQRS_REQUEST_CPU,
            CQRS_LIMIT_CPU,
        ),
        kv={
            "maxWorkers": CQRS_MAX_WORKERS,
            "remoteForensicMaxCoalesceRange": CQRS_REMOTE_FORENSIC_MAX_COALESCE_RANGE,
            "stagingChunkSize": CQRS_STAGING_CHUNK_SIZE,
            "bulkStagingMode": "force",
            "bulkStagingRowsPerPart": CQRS_BULK_STAGING_ROWS_PER_PART,
        },
    )


def createDemoPSP() -> YellowPlatformServiceProvider:
    merge_datacontainer = AzureSQLHyperscaleDatabase(
        "AzureHyperscaleMergeDB",
        hostPort=HostPortPair(AZURE_MERGE_SQL_SERVER_HOST, AZURE_SQL_SERVER_PORT),
        locations={_location()},
        productionStatus=ProductionStatus.NOT_PRODUCTION,
        databaseName=AZURE_MERGE_DBNAME,
        trustServerCertificate=AZURE_SQL_TRUST_SERVER_CERTIFICATE,
        # Headroom for the Azure SQL gateway login handshake under 200-way concurrency
        # (default 10s connect timeout expires as HYT00 before auth completes).
        dataContainerParams=DataContainerParams(loginTimeout=60),
    )

    cqrs_datacontainer = AzureSQLHyperscaleDatabase(
        CQRS_CONTAINER_NAME,
        hostPort=HostPortPair(AZURE_CQRS_SQL_SERVER_HOST, AZURE_SQL_SERVER_PORT),
        locations={_location()},
        productionStatus=ProductionStatus.NOT_PRODUCTION,
        databaseName=AZURE_CQRS_DBNAME,
        trustServerCertificate=AZURE_SQL_TRUST_SERVER_CERTIFICATE,
        dataContainerParams=DataContainerParams(loginTimeout=60),
    )

    git_config = GitCacheConfig(
        enabled=True,
        access_mode="ReadWriteMany",
        storage_size=StorageRequirement("100G"),
        storageClass="azurefile-csi-nfs",
    )

    yp_assembly = YellowAzureExternalAirflow3AndMergeDatabase(
        name="Demo",
        namespace=KUB_NAME_SPACE,
        git_cache_config=git_config,
        afHostPortPair=HostPortPair(AIRFLOW_HOST, AIRFLOW_PORT),
        airflowServiceAccount=AIRFLOW_SERVICE_ACCOUNT,
        externalSecretProvider=None,
    )

    return YellowPlatformServiceProvider(
        "SCD4_PSP",
        {_location()},
        PlainTextDocumentation("Azure concurrent-ingestion scale PSP"),
        gitCredential=Credential("git", CredentialType.API_TOKEN),
        mergeRW_Credential=Credential("sqlserver-demo-merge", CredentialType.USER_PASSWORD),
        yp_assembly=yp_assembly,
        merge_datacontainer=merge_datacontainer,
        pv_storage_class="azurefile-csi-nfs",
        datasurfaceDockerImage=f"registry.gitlab.com/datasurface-inc/datasurface/datasurface:v{DATASURFACE_VERSION}",
        bulkObjectStorage=_azure_bulk_binding(),
        hints=_ingestion_hints() + [_cqrs_hint()],
        # OTLP telemetry -> node-local OTel Collector DaemonSet (hostPort 4318) ->
        # AKS managed-metrics addon -> Azure Managed Prometheus -> Azure Managed Grafana.
        otlpEnabled=True,
        otlpPort=4318,
        otlpProtocol="http/protobuf",
        consumerReplicaGroups=[
            ConsumerReplicaGroup(
                name=CRG_NAME,
                dataContainers={cqrs_datacontainer},
                workspaceNames={CONSUMER_WORKSPACE_NAME},
                trigger=CronTrigger("Every minute", "* * * * *"),
                credential=Credential("sqlserver-cqrs", CredentialType.USER_PASSWORD),
                bulkObjectStorages={CQRS_CONTAINER_NAME: _azure_bulk_binding()},
            )
        ],
        dataPlatforms=[
            YellowDataPlatform(
                "SCD4",
                doc=PlainTextDocumentation("SCD4 Yellow DataPlatform"),
                milestoneStrategy=DataMilestoningStrategy.SCD4,
                stagingBatchesToKeep=5,
            )
        ],
    )


def createDemoRTE(ecosys: Ecosystem) -> RuntimeEnvironment:
    assert isinstance(ecosys.owningRepo, GitHubRepository)

    psp = createDemoPSP()
    rte = ecosys.getRuntimeEnvironmentOrThrow("demo")
    rte.configure(
        VersionPatternReleaseSelector(VersionPatterns.VN_N_N + "-demo", ReleaseType.STABLE_ONLY),
        [PSPDeclaration(psp.name, rte.owningRepo)],
        productionStatus=ProductionStatus.NOT_PRODUCTION,
    )
    rte.setPSP(psp)
    return rte
