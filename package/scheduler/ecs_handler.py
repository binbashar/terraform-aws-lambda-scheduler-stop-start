"""ECS service scheduler module."""

from typing import Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

from .exceptions import ecs_exception
from .filter_resources_by_tags import FilterByTags


class EcsScheduler:
    """Scheduler for ECS Services with tag-based filtering."""

    def __init__(self, region_name: Optional[str] = None) -> None:
        """Initialize ECS service scheduler.

        Args:
            region_name: AWS region name. If None, uses default region.
        """
        self.ecs = boto3.client("ecs", region_name=region_name) if region_name else boto3.client("ecs")
        self.tag_api = FilterByTags(region_name=region_name)

    def _parse_service_arn(self, service_arn: str) -> Tuple[str, str]:
        """Extract cluster and service names from service ARN.

        Args:
            service_arn: The ARN of the ECS service

        Returns:
            Tuple containing (cluster_name, service_name)
        """
        service_name = service_arn.split("/")[-1]
        cluster_name = service_arn.split("/")[-2]
        return cluster_name, service_name

    def _update_service_count(self, cluster_name: str, service_name: str, desired_count: int) -> None:
        """Update the desired count for an ECS service.

        Args:
            cluster_name: Name of the ECS cluster
            service_name: Name of the ECS service
            desired_count: Desired task count to set

        Raises:
            ClientError: If the ECS service update fails
        """
        try:
            self.ecs.update_service(
                cluster=cluster_name, 
                service=service_name, 
                desiredCount=desired_count
            )
            action = "Stop" if desired_count == 0 else "Start"
            print(f"{action} ECS Service {service_name} on Cluster {cluster_name}")
        except ClientError as exc:
            ecs_exception("ECS Service", service_name, exc)

    def stop(self, aws_tags: List[Dict]) -> None:
        """Stop ECS services with specified tags.

        Sets the desired count to 0 for all matching ECS services.

        Args:
            aws_tags: AWS tags to filter resources by.
                Example:
                [
                    {
                        'Key': 'string',
                        'Values': [
                            'string',
                        ]
                    }
                ]
        """
        for service_arn in self.tag_api.get_resources("ecs:service", aws_tags):
            cluster_name, service_name = self._parse_service_arn(service_arn)
            self._update_service_count(cluster_name, service_name, 0)

    def start(self, aws_tags: List[Dict]) -> None:
        """Start ECS services with specified tags.

        Sets the desired count to 1 for all matching ECS services.

        Args:
            aws_tags: AWS tags to filter resources by.
                Example:
                [
                    {
                        'Key': 'string',
                        'Values': [
                            'string',
                        ]
                    }
                ]
        """
        for service_arn in self.tag_api.get_resources("ecs:service", aws_tags):
            cluster_name, service_name = self._parse_service_arn(service_arn)
            self._update_service_count(cluster_name, service_name, 1)
