"""
aurekai_activities.py — Temporal activities wrapping all Akai capability families.
Each activity runs an akai CLI command and returns a typed AkaiResult.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any

from temporalio import activity


@dataclass
class AkaiResult:
    operator: str
    exit_code: int
    json_output: dict[str, Any] = field(default_factory=dict)
    proof_uri: str = ""
    artifact_id: str = ""

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


def _run_akai(args: list[str], timeout: int = 300) -> AkaiResult:
    operator = args[0] if args else "unknown"
    result = subprocess.run(
        ["akai", *args, "--json"],
        capture_output=True, text=True, timeout=timeout,
    )
    try:
        parsed = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        parsed = {"raw": result.stdout, "error": result.stderr}
    return AkaiResult(
        operator=operator,
        exit_code=result.returncode,
        json_output=parsed,
        proof_uri=parsed.get("proof_uri", ""),
        artifact_id=parsed.get("artifact_id", ""),
    )


# ── Runtime activities ───────────────────────────────────────────────────────

@activity.defn
async def doctor_deep() -> dict:
    activity.heartbeat("running doctor --deep")
    r = _run_akai(["doctor", "--deep"])
    if not r.ok:
        raise RuntimeError(f"doctor failed: {r.json_output}")
    return r.json_output


@activity.defn
async def runtime_capabilities() -> dict:
    return _run_akai(["runtime", "capabilities"]).json_output


@activity.defn
async def manifest_verify(manifest: str = "artifact.json") -> dict:
    r = _run_akai(["verify", "--manifest", manifest])
    if not r.ok:
        raise RuntimeError(f"manifest verify failed: {r.json_output}")
    return r.json_output


# ── Intake activities ────────────────────────────────────────────────────────

@activity.defn
async def transcribe_audio(audio_path: str, language: str = "en") -> dict:
    activity.heartbeat(f"transcribing {audio_path}")
    r = _run_akai(["transcribe", "audio", "--input", audio_path, "--language", language], timeout=600)
    if not r.ok:
        raise RuntimeError(f"transcribe failed: {r.json_output}")
    return r.json_output


@activity.defn
async def clean_transcript(transcript_id: str) -> dict:
    return _run_akai(["transcript", "clean", "--id", transcript_id]).json_output


@activity.defn
async def generate_brief(artifact_id: str) -> dict:
    return _run_akai(["brief", "generate", "--artifact", artifact_id]).json_output


@activity.defn
async def pack_deliverable(brief_id: str) -> dict:
    return _run_akai(["pack", "deliverable", "--brief", brief_id]).json_output


# ── Memory activities ────────────────────────────────────────────────────────

@activity.defn
async def fpq_compress(model_tag: str, bits: int = 8) -> dict:
    activity.heartbeat(f"compressing {model_tag} @ {bits}bits")
    r = _run_akai(["fpq", "compress", "--model", model_tag, "--bits", str(bits)], timeout=600)
    if not r.ok:
        raise RuntimeError(f"fpq compress failed: {r.json_output}")
    return r.json_output


@activity.defn
async def fpqx_align(model_tag: str) -> dict:
    activity.heartbeat(f"aligning {model_tag}")
    return _run_akai(["fpqx", "align", "--model", model_tag], timeout=600).json_output


@activity.defn
async def sli_auto_run() -> dict:
    activity.heartbeat("running SLI")
    return _run_akai(["sli", "auto-run"], timeout=600).json_output


@activity.defn
async def vec_search(query: str, top_k: int = 10) -> dict:
    return _run_akai(["vec", "search", "--query", query, "--top-k", str(top_k)]).json_output


# ── Proof activities ─────────────────────────────────────────────────────────

@activity.defn
async def proof_bundle(run_id: str) -> dict:
    r = _run_akai(["proof", "bundle", "--run-id", run_id])
    if not r.ok:
        raise RuntimeError(f"proof bundle failed: {r.json_output}")
    return r.json_output


@activity.defn
async def graph_lineage(artifact_id: str) -> dict:
    return _run_akai(["graph", "lineage", "--artifact", artifact_id]).json_output


# ── Commerce activities ──────────────────────────────────────────────────────

@activity.defn
async def meter_record(event: str, units: float = 1.0, client_id: str = "") -> dict:
    args = ["meter", "record", "--event", event, "--units", str(units)]
    if client_id:
        args += ["--client", client_id]
    return _run_akai(args).json_output


@activity.defn
async def generate_invoice(client_id: str, period: str = "current") -> dict:
    return _run_akai(["pay", "invoice", "--client", client_id, "--period", period]).json_output


@activity.defn
async def outreach_followup(client_id: str) -> dict:
    return _run_akai(["outreach", "followup", "--client", client_id]).json_output


# ── Wire activities ──────────────────────────────────────────────────────────

@activity.defn
async def wire_ingest_pcap(pcap_path: str) -> dict:
    activity.heartbeat(f"ingesting {pcap_path}")
    return _run_akai(["wire", "ingest-pcap", "--input", pcap_path]).json_output


@activity.defn
async def wire_report(capture_id: str) -> dict:
    return _run_akai(["wire", "report", "--capture", capture_id]).json_output


@activity.defn
async def tel_sim_call(target: str) -> dict:
    return _run_akai(["tel", "sim-call", "--target", target]).json_output


# ── Reason activities ────────────────────────────────────────────────────────

@activity.defn
async def reason_start(prompt: str = "") -> dict:
    args = ["reason", "start"]
    if prompt:
        args += ["--prompt", prompt]
    return _run_akai(args).json_output


@activity.defn
async def reason_branch(session_id: str) -> dict:
    return _run_akai(["reason", "branch", "--session", session_id]).json_output


@activity.defn
async def reason_diff(session_id: str) -> dict:
    return _run_akai(["reason", "diff", "--session", session_id]).json_output


# ── Release activities ───────────────────────────────────────────────────────

@activity.defn
async def release_gate(version: str, release_tag: str = "") -> dict:
    args = ["release", "gate", "--version", version]
    if release_tag:
        args += ["--tag", release_tag]
    r = _run_akai(args)
    if not r.ok:
        raise RuntimeError(f"release gate failed: {r.json_output}")
    return r.json_output
