"""Redshift cluster scheduler for managing stop/start operations."""

import logging
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from .exceptions import redshift_exception
from .filter_resources_by_tags import FilterByTags

# Configure logger
logger = logging.getLogger(__name__)


class RedshiftScheduler:
    """Manages scheduling operations for AWS Redshift clusters.

    This class provides functionality to stop and start Redshift clusters
    based on AWS resource tags.
    """

    def __init__(self, region_name: Optional[str] = None) -> None:
        """Initialize Redshift scheduler with appropriate AWS client.

        Args:
            region_name: Optional AWS region name. If not provided, the default
                         region from AWS configuration will be used.
        """
        self.redshift = boto3.client(
            "redshift", region_name=region_name if region_name else None
        )
        self.tag_api = FilterByTags(region_name=region_name)

    def _process_clusters(self, aws_tags: List[Dict], action: str) -> None:
        """Common method to process clusters based on the specified action.

        Args:
            aws_tags: List of AWS tag dictionaries to filter resources
            action: Action to perform ('stop' or 'start')
        """
        resource_type = "redshift:cluster"
        method_map = {
            "stop": self.redshift.pause_cluster,
            "start": self.redshift.resume_cluster,
        }

        if action not in method_map:
            logger.error(f"Invalid action: {action}. Must be 'stop' or 'start'.")
            return

        action_method = method_map[action]
        action_name = "Stop" if action == "stop" else "Start"

        for cluster_arn in self.tag_api.get_resources(resource_type, aws_tags):
            cluster_id = cluster_arn.split(":")[-1]
            try:
                action_method(ClusterIdentifier=cluster_id)
                logger.info(f"{action_name} redshift cluster {cluster_id}")
                print(f"{action_name} redshift cluster {cluster_id}")
            except ClientError as exc:
                redshift_exception("redshift cluster", cluster_id, exc)

    def stop(self, aws_tags: List[Dict]) -> None:
        """Stop Redshift clusters with the defined tags.

        Args:
            aws_tags: List of AWS tag dictionaries to filter resources.
                For example:
                [
                    {
                        'Key': 'Environment',
                        'Values': ['Development']
                    }
                ]
        """
        self._process_clusters(aws_tags, "stop")

    def start(self, aws_tags: List[Dict]) -> None:
        """Start Redshift clusters with the defined tags.

        Args:
            aws_tags: List of AWS tag dictionaries to filter resources.
                For example:
                [
                    {
                        'Key': 'Environment',
                        'Values': ['Development']
                    }
                ]
        """
        self._process_clusters(aws_tags, "start")
