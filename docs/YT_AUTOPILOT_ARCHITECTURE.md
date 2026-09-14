# YT Autopilot Repurpose

This module extends Cortex into a rights-first autonomous YouTube production pipeline.

## Non-negotiable gates

1. Online availability never implies reuse rights.
2. Only explicit public-domain, compatible Creative Commons, licensed, or user-authorized media may enter production.
3. Unknown or ambiguous rights block autonomous publishing.
4. DRM, paywalls, access controls, and platform restrictions are never bypassed.
5. Publishing requires both rights QC and content/originality QC.
6. YouTube credentials remain server-side and are injected through secrets/OAuth.

## Runtime topology

```text
Scheduler
   |
   v
Orchestrator --> Topic Research --> Topic Scoring
   |                                  |
   |                                  v
   +----------------------------> Media Discovery
                                      |
                                      v
                                Rights Verification
                                      |
                               [HARD GATE]
                                      |
                                      v
                              Media Ingestion/Analysis
                                      |
                       Research -> Script -> Fact Check
                                      |
                                      v
                                  TTS / Timing
                                      |
                                      v
                              Editorial Edit Planner
                                      |
                                      v
                              Deterministic FFmpeg
                                      |
                         +------------+------------+
                         |                         |
                     Captions                  Thumbnail
                         |                         |
                         +------------+------------+
                                      v
                                    SEO
                                      |
                                      v
                                      QC
                                      |
                              [HARD PUBLISH GATE]
                                      |
                                      v
                              YouTube API/OAuth
                                      |
                                      v
                              Analytics -> Learning
                                      |
                                      +----> next cycle
```

## State model

The persisted state machine is intentionally strict. A worker cannot jump directly from an idea to publication. Every transition is explicit and invalid transitions raise an error.

## Provider architecture

The core package contains protocols for LLM, TTS, media search/download, storage, and YouTube. Concrete integrations should live in adapters and must not be selected from arbitrary persisted strings. The worker registry should resolve only trusted, registered implementations.

## Data model

The planned PostgreSQL model maps to the requested entities: channels, settings, topics, research, sources, assets, rights, shots, scripts, narration, edit plans, videos, media links, music/SFX, thumbnails, metadata, publishing jobs, analytics, experiments, agent runs, errors, and audit logs.

## Rendering contract

AI produces an edit decision list; FFmpeg performs deterministic rendering. The editor should consume shot-level metadata, narration timings, rights-approved assets, pacing targets, audio mix targets, captions, and graphics instructions.

## Autonomous mode

Autonomous publishing remains disabled by default in the foundation. Production deployment should explicitly enable it only after OAuth, source licensing, quotas, storage, monitoring, and policy checks are configured. A global stop-publishing switch must be checked before every publish action.

## Next implementation phases

- PostgreSQL repositories and migrations
- Redis/Celery job queue with idempotency keys
- Media adapters for explicitly reusable sources
- ffprobe/FFmpeg worker
- shot detection and perceptual hashing
- LLM/TTS adapters
- YouTube OAuth/upload/analytics adapters
- thumbnail/SEO services
- dashboard and audit log UI
- end-to-end mocked pipeline
- containerized deployment and monitoring
