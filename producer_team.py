"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.
"""

from datasurface.containers import AzureSQLDatabase, HostPortPair, SQLCDCIngestion
from datasurface.documentation import PlainTextDocumentation
from datasurface.dsl import Datastore, Dataset, EnvRefDataContainer, EnvironmentMap, GovernanceZone, IngestionConsistencyType, ProductionStatus, Team
from datasurface.keys import LocationKey
from datasurface.policy import SimpleDC, SimpleDCTypes
from datasurface.schema import DDLColumn, DDLTable, NullableStatus, PrimaryKeyStatus
from datasurface.security import Credential, CredentialType
from datasurface.triggers import CronTrigger
from datasurface.types import Date, VarChar

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
                    DDLColumn("id", VarChar(20), nullable=NullableStatus.NOT_NULLABLE, primary_key=PrimaryKeyStatus.PK),
                    DDLColumn("firstName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("lastName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("dob", Date(), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("email", VarChar(100)),
                    DDLColumn("phone", VarChar(100)),
                    DDLColumn("primaryAddressId", VarChar(20)),
                    DDLColumn("billingAddressId", VarChar(20)),
                ]
            ),
            classifications=[SimpleDC(SimpleDCTypes.CPI, "Customer")],
        ),
        Dataset(
            "addresses",
            schema=DDLTable(
                columns=[
                    DDLColumn("id", VarChar(20), nullable=NullableStatus.NOT_NULLABLE, primary_key=PrimaryKeyStatus.PK),
                    DDLColumn("customerId", VarChar(20), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("streetName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("city", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("state", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                    DDLColumn("zipCode", VarChar(30), nullable=NullableStatus.NOT_NULLABLE),
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
                        CronTrigger("Every 5 minutes", "*/5 * * * *"),
                        IngestionConsistencyType.MULTI_DATASET,
                        Credential("customer-sqlserver-source-credential", CredentialType.USER_PASSWORD),
                    ),
                    datasets=customer_datasets(),
                )
            )
