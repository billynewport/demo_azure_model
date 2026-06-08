"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.
"""

from datasurface.documentation import PlainTextDocumentation
from datasurface.dsl import (
    ConsumerRetentionRequirements,
    DataLatency,
    DataMilestoningStrategy,
    DataPlatformManagedDataContainer,
    DatasetGroup,
    DatasetSink,
    GovernanceZone,
    Team,
    Workspace,
    WorkspacePlatformConfig,
)

from db_constants import CONSUMER_WORKSPACE_NAME, NUM_STORES_PER_TEAM, NUM_TEAMS
from producer_team import store_name


def createConsumerTeam(gz: GovernanceZone) -> None:
    team: Team = gz.getTeamOrThrow("consumerTeam")

    dsg_sinks: list[DatasetSink] = []
    for team_idx in range(1, NUM_TEAMS + 1):
        for store_idx in range(1, NUM_STORES_PER_TEAM + 1):
            generated_store_name = store_name(team_idx, store_idx)
            dsg_sinks.append(DatasetSink(generated_store_name, "customers"))
            dsg_sinks.append(DatasetSink(generated_store_name, "addresses"))

    team.add(
        Workspace(
            CONSUMER_WORKSPACE_NAME,
            DataPlatformManagedDataContainer("Azure scale consumer container"),
            PlainTextDocumentation("Workspace consuming all generated Azure SQL CDC datastores"),
            DatasetGroup(
                "SCD4_DSG",
                sinks=dsg_sinks,
                platform_chooser=WorkspacePlatformConfig(
                    hist=ConsumerRetentionRequirements(
                        r=DataMilestoningStrategy.SCD4,
                        latency=DataLatency.MINUTES,
                        regulator=None,
                    )
                ),
            ),
        )
    )
