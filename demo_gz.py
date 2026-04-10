"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.
"""

from datasurface.dsl import Ecosystem, GovernanceZone, TeamDeclaration
from datasurface.repos import GitHubRepository

GIT_REPO_OWNER: str = "billynewport"
GIT_REPO_NAME: str = "demo_azure_model"


def createDemoGZ(ecosys: Ecosystem) -> None:
    gz: GovernanceZone = ecosys.getZoneOrThrow("demo_gz")
    cred = ecosys.owningRepo.credential
    gz.add(TeamDeclaration(
        "producerTeam",
        GitHubRepository(f"{GIT_REPO_OWNER}/{GIT_REPO_NAME}", "producer_team_edit", credential=cred)
    ))
    gz.add(TeamDeclaration(
        "consumerTeam",
        GitHubRepository(f"{GIT_REPO_OWNER}/{GIT_REPO_NAME}", "consumer_team_edit", credential=cred)
    ))

    from producer_team import createProducerTeam
    from consumer_team import createConsumerTeam
    createProducerTeam(gz)
    createConsumerTeam(gz)
