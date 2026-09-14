# YT Autopilot Build Plan

## Phase 1 — Foundation
Implemented: rights-first domain objects, hard rights gate, topic scoring, originality/reuse scoring, fail-closed state machine, provider protocols, bounded orchestrator, and CI tests.

## Phase 2 — Persistence
PostgreSQL schema/migrations and repositories for channels, topics, research, sources, assets, rights, shots, scripts, narration, edit plans, videos, publishing, analytics, experiments, runs, errors and audit logs.

## Phase 3 — Workers
Redis/Celery queue, idempotency keys, retry/backoff, dead-letter handling and resumable jobs.

## Phase 4 — Media
Adapters for public-domain/licensed repositories, rights evidence, terms-respecting downloads, ffprobe metadata, shot detection and perceptual hashing.

## Phase 5 — Editorial AI
Research/source graph, original script generation, claim verification, narration timing, shot matching and edit decision lists.

## Phase 6 — Rendering
Deterministic FFmpeg rendering, captions, licensed music/SFX, loudness/clipping checks and programmatic graphics.

## Phase 7 — Packaging
Original thumbnail generation/selection, title/description/chapters, originality/reuse gates and full QC.

## Phase 8 — YouTube
OAuth adapter, upload/schedule/thumbnail/caption/playlist operations, quota-aware retry and server-side secret handling.

## Phase 9 — Learning
Analytics ingestion, experiments and channel strategy memory.

## Phase 10 — Operations
Dashboard, multi-channel configuration, cost controls, emergency stop, Docker deployment, backups and monitoring.

Every phase follows: implement → test → fix → document → commit. Publishing remains disabled until integration and rights tests pass.
