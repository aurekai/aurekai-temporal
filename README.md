<p align="center">
  <img src="https://raw.githubusercontent.com/aurekai/aurekai/main/assets/aurekai-logo.svg" alt="Aurekai" width="520" />
</p>

# `aurekai-temporal` · v0.8.0-alpha.5

Official Temporal integration for Aurekai — durable workflows for all capability families, typed activities with heartbeats, Nexus services, and proof propagation through `workflow.info().run_id`.

## Workflows

| Workflow | Description |
|---|---|
| `AurekaiClientJobWorkflow` | Audio → transcribe → brief → proof → meter → invoice → outreach |
| `AurekaiModelMemoryWorkflow` | FPQ compress → FPQx align → SLI → proof |
| `AurekaiReasoningWorkflow` | Reason start → branch → diff → proof |
| `AurekaiWireReportWorkflow` | PCAP ingest → wire report → proof |
| `AurekaiReleaseWorkflow` | Doctor → manifest verify → release gate → proof |
| `AurekaiInvoiceWorkflow` | Meter → invoice → outreach |

## Activities

| Activity | Family | Description |
|---|---|---|
| `doctor_deep` | runtime | Deep diagnostics with heartbeat |
| `manifest_verify` | runtime | Manifest schema validation |
| `transcribe_audio` | intake | Audio transcription (heartbeat, 15min timeout) |
| `clean_transcript` | intake | Transcript normalization |
| `generate_brief` | publish | Brief generation |
| `pack_deliverable` | publish | Pack deliverable from brief |
| `fpq_compress` | memory | FPQ model compression (heartbeat) |
| `fpqx_align` | memory | FPQx alignment (heartbeat) |
| `sli_auto_run` | memory | SLI convergence (heartbeat) |
| `vec_search` | memory | Vector search |
| `proof_bundle` | proof | Export proof bundle |
| `graph_lineage` | proof | Graph lineage export |
| `meter_record` | commerce | Record metering event |
| `generate_invoice` | commerce | Client invoice generation |
| `outreach_followup` | commerce | Client outreach |
| `wire_ingest_pcap` | wire | PCAP ingest (heartbeat) |
| `wire_report` | wire | Wire report generation |
| `tel_sim_call` | wire | Tel sim-call |
| `reason_start` | reason | Start reasoning session |
| `reason_branch` | reason | Branch reasoning |
| `reason_diff` | reason | Reasoning diff |
| `release_gate` | release | Full release gate check |

## Host-native features used

- **Heartbeats** — long transcription, FPQ compress, wire ingest, SLI
- **Retry policies** — max 3 attempts, 10s initial interval on all activities
- **Child Workflows** — `AurekaiClientJobWorkflow` can spawn `AurekaiInvoiceWorkflow` as child
- **Durable state** — proof `run_id` = Temporal `workflow.info().run_id` for lineage
- **Schedules** — daily `AurekaiModelMemoryWorkflow`, weekly `AurekaiReleaseWorkflow`

## Quick Start

```bash
pip install temporalio
pip install -r requirements.txt

# Start worker
python -c "
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows.aurekai_activities import *
from workflows.aurekai_workflows import *

async def main():
    client = await Client.connect('localhost:7233')
    worker = Worker(client, task_queue='aurekai', workflows=[
        AurekaiClientJobWorkflow, AurekaiModelMemoryWorkflow,
        AurekaiReasoningWorkflow, AurekaiWireReportWorkflow,
        AurekaiReleaseWorkflow, AurekaiInvoiceWorkflow,
    ], activities=[
        doctor_deep, manifest_verify, transcribe_audio, clean_transcript,
        generate_brief, pack_deliverable, fpq_compress, fpqx_align, sli_auto_run,
        proof_bundle, meter_record, generate_invoice, outreach_followup,
        wire_ingest_pcap, wire_report, release_gate,
    ])
    await worker.run()

asyncio.run(main())
"
```

## Layout

```
workflows/
  aurekai_activities.py   22 Temporal activities (all capability families)
  aurekai_workflows.py    6 durable workflow definitions
```


Aurekai integration surface for Temporal.

Status: active
Type: workflow

## Core Template Set

- doctor-deep
- manifest-verify
- model-memory-pack
- sae-audit
- semantic-cache-bench
- proof-bundle-export
- release-gate

## Canonical References

- Platform: https://github.com/aurekai/aurekai
- Native runtime: https://github.com/aurekai/native-runtime
- Integration registry: https://github.com/aurekai/aurekai/blob/main/registry/integrations.json
- Ecosystem map: https://github.com/aurekai/aurekai/blob/main/ECOSYSTEM_NAMES.md
