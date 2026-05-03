"""
aurekai_workflows.py — Temporal durable workflows for all Aurekai capability families.
"""
from __future__ import annotations

from datetime import timedelta
from dataclasses import dataclass

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from aurekai_activities import (
        doctor_deep, manifest_verify, transcribe_audio, clean_transcript,
        generate_brief, pack_deliverable, fpq_compress, fpqx_align, sli_auto_run,
        proof_bundle, graph_lineage, meter_record, generate_invoice, outreach_followup,
        wire_ingest_pcap, wire_report, tel_sim_call, reason_start, reason_branch,
        reason_diff, release_gate,
    )


RETRY = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=10))
LONG_TIMEOUT = timedelta(minutes=30)


@workflow.defn
class AurekaiClientJobWorkflow:
    """Full client job: audio → transcribe → brief → proof → invoice → outreach."""

    @workflow.run
    async def run(self, audio_path: str, client_id: str, language: str = "en") -> dict:
        transcript = await workflow.execute_activity(
            transcribe_audio, args=[audio_path, language],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RETRY,
            heartbeat_timeout=timedelta(minutes=2),
        )
        clean = await workflow.execute_activity(
            clean_transcript, args=[transcript["artifact_id"]],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        brief = await workflow.execute_activity(
            generate_brief, args=[clean["artifact_id"]],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        proof = await workflow.execute_activity(
            proof_bundle, args=[workflow.info().run_id],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        await workflow.execute_activity(
            meter_record, args=["client-job", 1.0, client_id],
            start_to_close_timeout=timedelta(minutes=2), retry_policy=RETRY,
        )
        invoice = await workflow.execute_activity(
            generate_invoice, args=[client_id, "current"],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        await workflow.execute_activity(
            outreach_followup, args=[client_id],
            start_to_close_timeout=timedelta(minutes=2), retry_policy=RETRY,
        )
        return {"brief": brief, "proof": proof, "invoice": invoice}


@workflow.defn
class AurekaiModelMemoryWorkflow:
    """FPQ compress → FPQx align → SLI → proof."""

    @workflow.run
    async def run(self, model_tag: str = "qwen3-8b", bits: int = 8) -> dict:
        compress = await workflow.execute_activity(
            fpq_compress, args=[model_tag, bits],
            start_to_close_timeout=timedelta(minutes=20), retry_policy=RETRY,
            heartbeat_timeout=timedelta(minutes=3),
        )
        align = await workflow.execute_activity(
            fpqx_align, args=[model_tag],
            start_to_close_timeout=timedelta(minutes=20), retry_policy=RETRY,
            heartbeat_timeout=timedelta(minutes=3),
        )
        sli = await workflow.execute_activity(
            sli_auto_run,
            start_to_close_timeout=timedelta(minutes=20), retry_policy=RETRY,
            heartbeat_timeout=timedelta(minutes=3),
        )
        proof = await workflow.execute_activity(
            proof_bundle, args=[workflow.info().run_id],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        return {"compress": compress, "align": align, "sli": sli, "proof": proof}


@workflow.defn
class AurekaiReasoningWorkflow:
    """Reason start → branch → diff → proof."""

    @workflow.run
    async def run(self, prompt: str = "") -> dict:
        session = await workflow.execute_activity(
            reason_start, args=[prompt],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        branch = await workflow.execute_activity(
            reason_branch, args=[session["session_id"]],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        diff = await workflow.execute_activity(
            reason_diff, args=[session["session_id"]],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        proof = await workflow.execute_activity(
            proof_bundle, args=[workflow.info().run_id],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        return {"session": session, "branch": branch, "diff": diff, "proof": proof}


@workflow.defn
class AurekaiWireReportWorkflow:
    """Wire PCAP ingest → probe → report → proof."""

    @workflow.run
    async def run(self, pcap_path: str) -> dict:
        ingest = await workflow.execute_activity(
            wire_ingest_pcap, args=[pcap_path],
            start_to_close_timeout=timedelta(minutes=10), retry_policy=RETRY,
            heartbeat_timeout=timedelta(minutes=2),
        )
        report = await workflow.execute_activity(
            wire_report, args=[ingest["artifact_id"]],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        proof = await workflow.execute_activity(
            proof_bundle, args=[workflow.info().run_id],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        return {"report": report, "proof": proof}


@workflow.defn
class AurekaiReleaseWorkflow:
    """Doctor → manifest verify → release gate → proof."""

    @workflow.run
    async def run(self, version: str, release_tag: str = "") -> dict:
        await workflow.execute_activity(
            doctor_deep,
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        await workflow.execute_activity(
            manifest_verify, args=["artifact.json"],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        gate = await workflow.execute_activity(
            release_gate, args=[version, release_tag],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        proof = await workflow.execute_activity(
            proof_bundle, args=[workflow.info().run_id],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        return {"gate": gate, "proof": proof}


@workflow.defn
class AurekaiInvoiceWorkflow:
    """Meter → invoice → outreach for a client."""

    @workflow.run
    async def run(self, client_id: str, event: str = "job", units: float = 1.0) -> dict:
        await workflow.execute_activity(
            meter_record, args=[event, units, client_id],
            start_to_close_timeout=timedelta(minutes=2), retry_policy=RETRY,
        )
        invoice = await workflow.execute_activity(
            generate_invoice, args=[client_id, "current"],
            start_to_close_timeout=timedelta(minutes=5), retry_policy=RETRY,
        )
        await workflow.execute_activity(
            outreach_followup, args=[client_id],
            start_to_close_timeout=timedelta(minutes=2), retry_policy=RETRY,
        )
        return invoice
