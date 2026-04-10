"""
Copyright (c) 2026 DataSurface Inc. All Rights Reserved.
Proprietary Software - See LICENSE.txt for terms.

Azure AKS nightly test ecosystem.
"""

from datasurface.dsl import InfrastructureVendor, InfrastructureLocation, Ecosystem, CloudVendor, RuntimeDeclaration, GovernanceZoneDeclaration
from datasurface.security import Credential, CredentialType
from datasurface.documentation import PlainTextDocumentation
from datasurface.repos import GitHubRepository
from rte_azure import createDemoRTE
from demo_gz import createDemoGZ

GIT_REPO_OWNER: str = "billynewport"
GIT_REPO_NAME: str = "demo_azure_model"


def createEcosystem() -> Ecosystem:
    """Azure nightly test ecosystem with PostgreSQL snapshot + SQL Server CDC ingestion."""

    git: Credential = Credential("git", CredentialType.API_TOKEN)
    eRepo: GitHubRepository = GitHubRepository(f"{GIT_REPO_OWNER}/{GIT_REPO_NAME}", "main", credential=git)

    ecosys: Ecosystem = Ecosystem(
        name="Demo",
        repo=eRepo,
        runtimeDecls=[
            RuntimeDeclaration("demo", GitHubRepository(f"{GIT_REPO_OWNER}/{GIT_REPO_NAME}", "demo_rte_edit", credential=git))
        ],
        infrastructure_vendors=[
            InfrastructureVendor(
                name="MyCorp",
                cloud_vendor=CloudVendor.PRIVATE,
                documentation=PlainTextDocumentation("Private company data centers"),
                locations=[
                    InfrastructureLocation(
                        name="USA",
                        locations=[
                            InfrastructureLocation(name="NY_1")
                        ]
                    )
                ]
            )
        ],
        governance_zone_declarations=[
            GovernanceZoneDeclaration("demo_gz", GitHubRepository(f"{GIT_REPO_OWNER}/{GIT_REPO_NAME}", "demo_gz_edit", credential=git))
        ],
        liveRepo=GitHubRepository(f"{GIT_REPO_OWNER}/{GIT_REPO_NAME}", "main", credential=git)
    )
    # Define the demo RTE
    createDemoRTE(ecosys)
    # Define the demo GZ/teams
    createDemoGZ(ecosys)
    return ecosys
