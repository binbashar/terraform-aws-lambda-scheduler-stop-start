"""DocumentDB instances scheduler for starting and stopping clusters."""

import logging
from enum import Enum
from typing import Dict, List, Literal, Optional, Union

import boto3
from botocore.exceptions import ClientError

from .exceptions import documentdb_exception
from .filter_resources_by_tags import FilterByTags

logger = logging.getLogger(__name__)


class ClusterAction(Enum):
    """DocumentDB cluster actions."""

    START = "start"
    STOP = "stop"


class DocumentDBScheduler:
    """DocumentDB scheduler for managing cluster state based on tags."""

    def __init__(self, region_name: Optional[str] = None) -> None:
        """Initialize DocumentDB scheduler.

        Args:
            region_name: AWS region name. If None, uses default region.
        """
        self.documentdb = boto3.client(
            "docdb", region_name=region_name if region_name else None
        )
        self.tag_api = FilterByTags(region_name=region_name)

    def _manage_cluster(self, action: ClusterAction, cluster_id: str) -> bool:
        """Perform start or stop action on a DocumentDB cluster.

        Args:
            action: The action to perform (START or STOP)
            cluster_id: The DocumentDB cluster identifier

        Returns:
            bool: True if action was successful, False otherwise
        """
        try:
            if action == ClusterAction.START:
                self.documentdb.start_db_cluster(DBClusterIdentifier=cluster_id)
                logger.info(f"Started DocumentDB cluster: {cluster_id}")
            elif action == ClusterAction.STOP:
                self.documentdb.stop_db_cluster(DBClusterIdentifier=cluster_id)
                logger.info(f"Stopped DocumentDB cluster: {cluster_id}")
            return True
        except ClientError as exc:
            documentdb_exception("DocumentDB cluster", cluster_id, exc)
            return False

    def _process_clusters(self, action: ClusterAction, aws_tags: List[Dict]) -> None:
        """Process DocumentDB clusters with the specified action.

        Args:
            action: The action to perform (START or STOP)
            aws_tags: AWS tags to filter resources
        """
        for cluster_arn in self.tag_api.get_resources("rds:cluster", aws_tags):
            cluster_id = cluster_arn.split(":")[-1]
            self._manage_cluster(action, cluster_id)

    def stop(self, aws_tags: List[Dict]) -> None:
        """Stop DocumentDB clusters with the specified tags.

        Args:
            aws_tags: AWS tags to filter resources
                Example:
                [
                    {
                        'Key': 'string',
                        'Values': ['string']
                    }
                ]
        """
        self._process_clusters(ClusterAction.STOP, aws_tags)

    def start(self, aws_tags: List[Dict]) -> None:
        """Start DocumentDB clusters with the specified tags.

        Args:
            aws_tags: AWS tags to filter resources
                Example:
                [
                    {
                        'Key': 'string',
                        'Values': ['string']
                    }
                ]
        """
        self._process_clusters(ClusterAction.START, aws_tags)
