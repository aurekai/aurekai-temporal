#!/usr/bin/env python3
"""Aurekai Temporal workflow — core pipeline."""
import subprocess
from datetime import timedelta
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


@activity.defn
async def run_akai(cmd: list[str]) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True)
    return out.stdout + out.stderr


@workflow.defn
class AurekaiCorePipeline:
    @workflow.run
    async def run(self) -> str:
        doctor = await workflow.execute_activity(
            run_akai, ["akai", "doctor", "--deep", "--json"],
            schedule_to_close_timeout=timedelta(minutes=5)
        )
        verify = await workflow.execute_activity(
            run_akai, ["akai", "verify", "--manifest", "artifact.json", "--json"],
            schedule_to_close_timeout=timedelta(minutes=5)
        )
        gate = await workflow.execute_activity(
            run_akai, ["akai", "release", "gate", "--version", "0.8.0-alpha.4", "--json"],
            schedule_to_close_timeout=timedelta(minutes=5)
        )
        return gate
