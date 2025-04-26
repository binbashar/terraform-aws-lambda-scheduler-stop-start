"""Cloudwatch alarm action scheduler."""

from typing import Dict, List, Optional
import logging

import boto3
from botocore.exceptions import ClientError

from .exceptions import cloudwatch_exception
from .filter_resources_by_tags import FilterByTags


class CloudWatchAlarmScheduler:
    """CloudWatch alarm scheduler for enabling/disabling alarm actions based on tags.

    This class provides functionality to start (enable) or stop (disable) CloudWatch
    alarm actions that match specific AWS resource tags.
    """

    def __init__(self, region_name: Optional[str] = None) -> None:
        """Initialize CloudWatch alarm scheduler with the specified AWS region.

        Args:
            region_name: Optional AWS region name. If not provided, the default
                         region from AWS configuration will be used.
        """
        self.cloudwatch = (
            boto3.client("cloudwatch", region_name=region_name)
            if region_name
            else boto3.client("cloudwatch")
        )
        self.tag_api = FilterByTags(region_name=region_name)
        self.logger = logging.getLogger(__name__)

    def _process_alarms(self, aws_tags: List[Dict], enable: bool) -> None:
        """Process CloudWatch alarms by enabling or disabling them.

        Args:
            aws_tags: AWS tags to filter resources by
            enable: True to enable alarms, False to disable alarms
        """
        action = "enable" if enable else "disable"
        method = (
            self.cloudwatch.enable_alarm_actions
            if enable
            else self.cloudwatch.disable_alarm_actions
        )
        action_present = "Enabling" if enable else "Disabling"
        action_past = "Enabled" if enable else "Disabled"

        for alarm_arn in self.tag_api.get_resources("cloudwatch:alarm", aws_tags):
            alarm_name = alarm_arn.split(":")[-1]
            try:
                method(AlarmNames=[alarm_name])
                self.logger.info(f"{action_past} CloudWatch alarm {alarm_name}")
                print(f"{action_past} CloudWatch alarm {alarm_name}")
            except ClientError as exc:
                cloudwatch_exception("cloudwatch alarm", alarm_name, exc)

    def stop(self, aws_tags: List[Dict]) -> None:
        """Disable CloudWatch alarm actions for resources with the specified tags.

        Args:
            aws_tags: AWS tags to filter resources by.
                      Format: [{'Key': 'tag_key', 'Values': ['tag_value', ...]}]
        """
        self._process_alarms(aws_tags, enable=False)

    def start(self, aws_tags: List[Dict]) -> None:
        """Enable CloudWatch alarm actions for resources with the specified tags.

        Args:
            aws_tags: AWS tags to filter resources by.
                      Format: [{'Key': 'tag_key', 'Values': ['tag_value', ...]}]
        """
        self._process_alarms(aws_tags, enable=True)
