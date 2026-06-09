"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.
"""

from datasurface.containers import AzureSQLDatabase, DataContainerParams, HostPortPair, SQLCDCIngestion
from datasurface.documentation import PlainTextDocumentation
from datasurface.dsl import Datastore, Dataset, EnvRefDataContainer, EnvironmentMap, GovernanceZone, IngestionConsistencyType, ProductionStatus, Team
from datasurface.keys import LocationKey
from datasurface.policy import SimpleDC, SimpleDCTypes
from datasurface.schema import DDLColumn, DDLTable, NullableStatus, PrimaryKeyStatus
from datasurface.security import Credential, CredentialType
from datasurface.triggers import CronTrigger
from datasurface.types import Date, NVarChar

from db_constants import (
    AZURE_LOCATION_KEY,
    AZURE_SOURCE_DBNAME,
    AZURE_SOURCE_SQL_SERVER_HOST,
    AZURE_SQL_SERVER_PORT,
    AZURE_SQL_TRUST_SERVER_CERTIFICATE,
    NUM_STORES_PER_TEAM,
    NUM_TEAMS,
)


SOURCE_CONTAINER_REF: str = "customer_db_azuresql"


def store_name(team_idx: int, store_idx: int) -> str:
    return f"CustomerDB_AzureSQL_T{team_idx}_{store_idx}"


def customer_datasets() -> list[Dataset]:
    return [
        Dataset(
            "customers",
            schema=DDLTable(
                columns=[
                    DDLColumn("id", NVarChar(20), nullable=NullableStatus.NOT_NULLABLE, primary_key=PrimaryKeyStatus.PK),
                    DDLColumn("firstName", NVarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("lastName", NVarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("dob", Date(), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("email", NVarChar(100)),
                    DDLColumn("phone", NVarChar(100)),
                    DDLColumn("primaryAddressId", NVarChar(20)),
                    DDLColumn("billingAddressId", NVarChar(20)),
                ]
            ),
            classifications=[SimpleDC(SimpleDCTypes.CPI, "Customer")],
        ),
        Dataset(
            "addresses",
            schema=DDLTable(
                columns=[
                    DDLColumn("id", NVarChar(20), nullable=NullableStatus.NOT_NULLABLE, primary_key=PrimaryKeyStatus.PK),
                    DDLColumn("customerId", NVarChar(20), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("streetName", NVarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("city", NVarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("state", NVarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("zipCode", NVarChar(30), nullable=NullableStatus.NOT_NULLABLE),
                ]
            ),
            classifications=[SimpleDC(SimpleDCTypes.CPI, "Address")],
        ),
    ]


def createProducerTeam(gz: GovernanceZone) -> None:
    producer_team: Team = gz.getTeamOrThrow("producerTeam")
    producer_team.add(
        EnvironmentMap(
            "demo",
            dataContainers={
                frozenset([SOURCE_CONTAINER_REF]): AzureSQLDatabase(
                    "CustomerDB_AzureSQL",
                    hostPort=HostPortPair(AZURE_SOURCE_SQL_SERVER_HOST, AZURE_SQL_SERVER_PORT),
                    locations={LocationKey(AZURE_LOCATION_KEY)},
                    productionStatus=ProductionStatus.NOT_PRODUCTION,
                    databaseName=AZURE_SOURCE_DBNAME,
                    trustServerCertificate=AZURE_SQL_TRUST_SERVER_CERTIFICATE,
                    # High-concurrency ingestion pods overwhelm the Azure SQL gateway login
                    # handshake; the default 10s connect timeout expires (HYT00) before the
                    # gateway authenticates. Give logins headroom under burst.
                    dataContainerParams=DataContainerParams(loginTimeout=60),
                )
            },
            dtReleaseSelectors=dict(),
            dtDockerImages=dict(),
        )
    )

    for team_idx in range(1, NUM_TEAMS + 1):
        for store_idx in range(1, NUM_STORES_PER_TEAM + 1):
            producer_team.add(
                Datastore(
                    store_name(team_idx, store_idx),
                    documentation=PlainTextDocumentation("Azure SQL CDC scale-test datastore"),
                    capture_metadata=SQLCDCIngestion(
                        EnvRefDataContainer(SOURCE_CONTAINER_REF),
                        CronTrigger("Every minute", "* * * * *"),
                        IngestionConsistencyType.MULTI_DATASET,
                        Credential("customer-sqlserver-source-credential", CredentialType.USER_PASSWORD),
                    ),
                    datasets=customer_datasets(),
                )
            )
