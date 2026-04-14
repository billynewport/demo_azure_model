"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.
"""

from datasurface.dsl import GovernanceZone, Team, EnvironmentMap, Datastore, Dataset
from datasurface.schema import DDLTable, DDLColumn, NullableStatus, PrimaryKeyStatus
from datasurface.containers import SQLSnapshotIngestion, HostPortPair, PostgresDatabase
from datasurface.dsl import EnvRefDataContainer, IngestionConsistencyType, ProductionStatus
from datasurface.md.db.sqlserver import SQLServerDatabase
from datasurface.triggers import CronTrigger
from datasurface.security import Credential, CredentialType
from datasurface.documentation import PlainTextDocumentation
from datasurface.policy import SimpleDC, SimpleDCTypes
from datasurface.types import VarChar, Date
from datasurface.keys import LocationKey


def createProducerTeam(gz: GovernanceZone) -> None:
    producerTeam: Team = gz.getTeamOrThrow("producerTeam")
    producerTeam.add(
        EnvironmentMap(
            "demo",
            dataContainers={
                frozenset(["customer_db"]): PostgresDatabase(
                    "CustomerDB",
                    hostPort=HostPortPair("ds-nightly-test-pgflex.postgres.database.azure.com", 5432),
                    locations={LocationKey("MyCorp:USA/NY_1")},
                    productionStatus=ProductionStatus.NOT_PRODUCTION,
                    databaseName="customer_db"
                ),
                frozenset(["customer_db_sqlserver"]): SQLServerDatabase(
                    "CustomerDB",
                    hostPort=HostPortPair("ds-nightly-test-sqlserver.database.windows.net", 1433),
                    locations={LocationKey("MyCorp:USA/NY_1")},
                    productionStatus=ProductionStatus.NOT_PRODUCTION,
                    databaseName="customer_db",
                    trustServerCertificate=True
                )
            },
            dtReleaseSelectors=dict(),
            dtDockerImages=dict()
        ),
        Datastore(
            "CustomerDB",
            documentation=PlainTextDocumentation("Postgres customer datastore ingested via SQLSnapshot"),
            capture_metadata=SQLSnapshotIngestion(
                EnvRefDataContainer("customer_db"),
                CronTrigger("Every 2 minute", "*/2 * * * *"),
                IngestionConsistencyType.MULTI_DATASET,
                Credential("customer-source-credential", CredentialType.USER_PASSWORD),
            ),
            datasets=[
                Dataset(
                    "customers",
                    schema=DDLTable(columns=[
                        DDLColumn("id", VarChar(20), nullable=NullableStatus.NOT_NULLABLE, primary_key=PrimaryKeyStatus.PK),
                        DDLColumn("firstName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("lastName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("dob", Date(), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("email", VarChar(100)),
                        DDLColumn("phone", VarChar(100)),
                        DDLColumn("primaryAddressId", VarChar(20)),
                        DDLColumn("billingAddressId", VarChar(20)),
                    ]),
                    classifications=[SimpleDC(SimpleDCTypes.CPI, "Customer")]
                ),
                Dataset(
                    "addresses",
                    schema=DDLTable(columns=[
                        DDLColumn("id", VarChar(20), nullable=NullableStatus.NOT_NULLABLE, primary_key=PrimaryKeyStatus.PK),
                        DDLColumn("customerId", VarChar(20), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("streetName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("city", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("state", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("zipCode", VarChar(30), nullable=NullableStatus.NOT_NULLABLE),
                    ]),
                    classifications=[SimpleDC(SimpleDCTypes.CPI, "Address")]
                )
            ]
        ),
        Datastore(
            "CustomerDB_SQLServer",
            documentation=PlainTextDocumentation("SQL Server customer datastore ingested via SQLCDC"),
            capture_metadata=SQLSnapshotIngestion(
                EnvRefDataContainer("customer_db_sqlserver"),
                CronTrigger("Every 2 minute", "*/2 * * * *"),
                IngestionConsistencyType.MULTI_DATASET,
                Credential("customer-sqlserver-source-credential", CredentialType.USER_PASSWORD),
            ),
            datasets=[
                Dataset(
                    "customers",
                    schema=DDLTable(columns=[
                        DDLColumn("id", VarChar(20), nullable=NullableStatus.NOT_NULLABLE, primary_key=PrimaryKeyStatus.PK),
                        DDLColumn("firstName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("lastName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("dob", Date(), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("email", VarChar(100)),
                        DDLColumn("phone", VarChar(100)),
                        DDLColumn("primaryAddressId", VarChar(20)),
                        DDLColumn("billingAddressId", VarChar(20)),
                    ]),
                    classifications=[SimpleDC(SimpleDCTypes.CPI, "Customer")]
                ),
                Dataset(
                    "addresses",
                    schema=DDLTable(columns=[
                        DDLColumn("id", VarChar(20), nullable=NullableStatus.NOT_NULLABLE, primary_key=PrimaryKeyStatus.PK),
                        DDLColumn("customerId", VarChar(20), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("streetName", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("city", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("state", VarChar(100), nullable=NullableStatus.NOT_NULLABLE),
                        DDLColumn("zipCode", VarChar(30), nullable=NullableStatus.NOT_NULLABLE),
                    ]),
                    classifications=[SimpleDC(SimpleDCTypes.CPI, "Address")]
                )
            ]
        )
    )
