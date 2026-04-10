"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.

Azure AKS runtime environment configuration for DataSurface Yellow nightly test.
"""

from datasurface.dsl import ProductionStatus, \
    RuntimeEnvironment, Ecosystem, PSPDeclaration, \
    DataMilestoningStrategy, ConsumerReplicaGroup
from datasurface.keys import LocationKey
from datasurface.containers import HostPortPair
from datasurface.md.db.sqlserver import SQLServerDatabase
from datasurface.security import Credential, CredentialType
from datasurface.documentation import PlainTextDocumentation
from datasurface.platforms.yellow import YellowDataPlatform, YellowPlatformServiceProvider
from datasurface.platforms.yellow.azure_assembly import YellowAzureExternalAirflow3AndMergeDatabase
from datasurface.platforms.yellow.assembly import GitCacheConfig
from datasurface.repos import VersionPatternReleaseSelector, GitHubRepository, ReleaseType, VersionPatterns
from datasurface.triggers import CronTrigger

# Azure configuration - hardcoded values for AKS nightly test
KUB_NAME_SPACE: str = "ds-nightly"
MERGE_HOST: str = "ds-nightly-test-sqlserver.database.windows.net"
MERGE_PORT: int = 1433
MERGE_DBNAME: str = "merge_db"
AIRFLOW_HOST: str = "ds-nightly-test-pgflex.postgres.database.azure.com"
AIRFLOW_PORT: int = 5432
AIRFLOW_SERVICE_ACCOUNT: str = "airflow-worker"
DATASURFACE_VERSION: str = "1.3.2"


def createDemoPSP() -> YellowPlatformServiceProvider:
    # Azure SQL merge database
    k8s_merge_datacontainer: SQLServerDatabase = SQLServerDatabase(
        "K8sMergeDB",
        hostPort=HostPortPair(MERGE_HOST, MERGE_PORT),
        locations={LocationKey("MyCorp:USA/NY_1")},
        productionStatus=ProductionStatus.NOT_PRODUCTION,
        databaseName=MERGE_DBNAME,
        trustServerCertificate=True
    )

    git_config: GitCacheConfig = GitCacheConfig(
        enabled=True,
        access_mode="ReadWriteMany",
        storageClass="azurefile-csi-nfs"
    )

    yp_assembly: YellowAzureExternalAirflow3AndMergeDatabase = YellowAzureExternalAirflow3AndMergeDatabase(
        name="Demo",
        namespace=KUB_NAME_SPACE,
        git_cache_config=git_config,
        afHostPortPair=HostPortPair(AIRFLOW_HOST, AIRFLOW_PORT),
        airflowServiceAccount=AIRFLOW_SERVICE_ACCOUNT
    )

    psp: YellowPlatformServiceProvider = YellowPlatformServiceProvider(
        "Demo_PSP",
        {LocationKey("MyCorp:USA/NY_1")},
        PlainTextDocumentation("Azure nightly test PSP"),
        gitCredential=Credential("git", CredentialType.API_TOKEN),
        mergeRW_Credential=Credential("sqlserver-demo-merge", CredentialType.USER_PASSWORD),
        yp_assembly=yp_assembly,
        merge_datacontainer=k8s_merge_datacontainer,
        pv_storage_class="azurefile-csi-nfs",
        datasurfaceDockerImage=f"registry.gitlab.com/datasurface-inc/datasurface/datasurface:v{DATASURFACE_VERSION}",
        consumerReplicaGroups=[
            ConsumerReplicaGroup(
                name="SQLServerCQRS",
                dataContainers={
                    SQLServerDatabase(
                        "SQLServer_CQRS_DB",
                        hostPort=HostPortPair(MERGE_HOST, MERGE_PORT),
                        locations={LocationKey("MyCorp:USA/NY_1")},
                        productionStatus=ProductionStatus.NOT_PRODUCTION,
                        databaseName="cqrs_db",
                        trustServerCertificate=True
                    )
                },
                workspaceNames={"ConsumerPostgres", "ConsumerCDC"},
                trigger=CronTrigger("Every 2 minute", "*/2 * * * *"),
                credential=Credential("sqlserver-demo-merge", CredentialType.USER_PASSWORD)
            )
        ],
        dataPlatforms=[
            YellowDataPlatform(
                "SCD2",
                doc=PlainTextDocumentation("SCD2 Yellow DataPlatform"),
                milestoneStrategy=DataMilestoningStrategy.SCD2,
                stagingBatchesToKeep=5
            )
        ]
    )
    return psp


def createDemoRTE(ecosys: Ecosystem) -> RuntimeEnvironment:
    assert isinstance(ecosys.owningRepo, GitHubRepository)

    psp: YellowPlatformServiceProvider = createDemoPSP()
    rte: RuntimeEnvironment = ecosys.getRuntimeEnvironmentOrThrow("demo")
    rte.configure(VersionPatternReleaseSelector(
        VersionPatterns.VN_N_N + "-demo", ReleaseType.STABLE_ONLY),
        [PSPDeclaration(psp.name, rte.owningRepo)],
        productionStatus=ProductionStatus.NOT_PRODUCTION)
    rte.setPSP(psp)
    return rte
