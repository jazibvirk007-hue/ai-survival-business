-- YT Autopilot durable state. PostgreSQL 14+.
-- All identifiers are UUID/text so this migration can coexist with Cortex.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS yt_channels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  youtube_channel_id TEXT,
  niche TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'en',
  mode TEXT NOT NULL DEFAULT 'DOCUMENTARY',
  settings JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS yt_topics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID NOT NULL REFERENCES yt_channels(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  score NUMERIC(6,2) NOT NULL DEFAULT 0,
  score_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'IDEA',
  research JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS yt_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_url TEXT NOT NULL,
  source_name TEXT NOT NULL,
  creator TEXT NOT NULL DEFAULT '',
  local_uri TEXT,
  sha256 TEXT,
  perceptual_hash TEXT,
  mime_type TEXT,
  duration_seconds NUMERIC(12,3) NOT NULL DEFAULT 0,
  width INTEGER NOT NULL DEFAULT 0,
  height INTEGER NOT NULL DEFAULT 0,
  fps NUMERIC(8,3) NOT NULL DEFAULT 0,
  has_audio BOOLEAN NOT NULL DEFAULT false,
  analysis JSONB NOT NULL DEFAULT '{}'::jsonb,
  usage_count INTEGER NOT NULL DEFAULT 0,
  disabled BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS yt_assets_sha256_uq ON yt_assets(sha256) WHERE sha256 IS NOT NULL;
CREATE INDEX IF NOT EXISTS yt_assets_phash_idx ON yt_assets(perceptual_hash) WHERE perceptual_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS yt_asset_rights (
  asset_id UUID PRIMARY KEY REFERENCES yt_assets(id) ON DELETE CASCADE,
  license TEXT NOT NULL DEFAULT '',
  license_url TEXT NOT NULL DEFAULT '',
  usage_restrictions TEXT NOT NULL DEFAULT '',
  commercial_use_allowed BOOLEAN NOT NULL DEFAULT false,
  modification_allowed BOOLEAN NOT NULL DEFAULT false,
  attribution_required BOOLEAN NOT NULL DEFAULT false,
  attribution_text TEXT NOT NULL DEFAULT '',
  verification_status TEXT NOT NULL DEFAULT 'UNKNOWN',
  verified_at TIMESTAMPTZ,
  download_date TIMESTAMPTZ,
  evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (verification_status IN ('VERIFIED_REUSABLE','REQUIRES_ATTRIBUTION','REQUIRES_PERMISSION','UNKNOWN','REJECTED'))
);

CREATE TABLE IF NOT EXISTS yt_shots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES yt_assets(id) ON DELETE CASCADE,
  start_seconds NUMERIC(12,3) NOT NULL,
  end_seconds NUMERIC(12,3) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  quality_score NUMERIC(6,2) NOT NULL DEFAULT 0,
  relevance_score NUMERIC(6,2) NOT NULL DEFAULT 0,
  features JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (end_seconds > start_seconds)
);

CREATE TABLE IF NOT EXISTS yt_scripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id UUID NOT NULL REFERENCES yt_topics(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  body TEXT NOT NULL,
  claims JSONB NOT NULL DEFAULT '[]'::jsonb,
  fact_status TEXT NOT NULL DEFAULT 'UNCERTAIN',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(topic_id, version)
);

CREATE TABLE IF NOT EXISTS yt_narration (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  script_id UUID NOT NULL REFERENCES yt_scripts(id) ON DELETE CASCADE,
  storage_uri TEXT NOT NULL,
  duration_seconds NUMERIC(12,3) NOT NULL DEFAULT 0,
  word_timestamps JSONB NOT NULL DEFAULT '[]'::jsonb,
  voice_provider TEXT NOT NULL,
  voice_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS yt_edit_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  script_id UUID NOT NULL REFERENCES yt_scripts(id) ON DELETE CASCADE,
  plan JSONB NOT NULL,
  originality_score NUMERIC(6,2) NOT NULL DEFAULT 0,
  reused_content_risk NUMERIC(6,2) NOT NULL DEFAULT 100,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS yt_videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID NOT NULL REFERENCES yt_channels(id) ON DELETE CASCADE,
  topic_id UUID REFERENCES yt_topics(id),
  state TEXT NOT NULL DEFAULT 'IDEA',
  render_uri TEXT,
  duration_seconds NUMERIC(12,3) NOT NULL DEFAULT 0,
  qc_report JSONB NOT NULL DEFAULT '{}'::jsonb,
  rights_ok BOOLEAN NOT NULL DEFAULT false,
  originality_score NUMERIC(6,2) NOT NULL DEFAULT 0,
  reused_content_risk NUMERIC(6,2) NOT NULL DEFAULT 100,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS yt_video_assets (
  video_id UUID NOT NULL REFERENCES yt_videos(id) ON DELETE CASCADE,
  asset_id UUID NOT NULL REFERENCES yt_assets(id),
  role TEXT NOT NULL,
  usage_count INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY(video_id, asset_id, role)
);

CREATE TABLE IF NOT EXISTS yt_thumbnails (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES yt_videos(id) ON DELETE CASCADE,
  variant TEXT NOT NULL,
  storage_uri TEXT NOT NULL,
  score NUMERIC(6,2) NOT NULL DEFAULT 0,
  accuracy_ok BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS yt_metadata (
  video_id UUID PRIMARY KEY REFERENCES yt_videos(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  category_id TEXT,
  chapters JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS yt_publishing_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES yt_videos(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'QUEUED',
  mode TEXT NOT NULL DEFAULT 'SCHEDULED',
  scheduled_for TIMESTAMPTZ,
  youtube_video_id TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS yt_analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES yt_videos(id) ON DELETE CASCADE,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metrics JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS yt_experiments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID NOT NULL REFERENCES yt_channels(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  variants JSONB NOT NULL,
  result JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'RUNNING'
);

CREATE TABLE IF NOT EXISTS yt_agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID REFERENCES yt_channels(id),
  agent TEXT NOT NULL,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL,
  input JSONB NOT NULL DEFAULT '{}'::jsonb,
  output JSONB NOT NULL DEFAULT '{}'::jsonb,
  error TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS yt_errors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID,
  error_type TEXT NOT NULL,
  message TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS yt_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID REFERENCES yt_channels(id),
  actor TEXT NOT NULL DEFAULT 'system',
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS yt_runtime_controls (
  singleton BOOLEAN PRIMARY KEY DEFAULT true CHECK (singleton),
  pause_all BOOLEAN NOT NULL DEFAULT false,
  stop_publishing BOOLEAN NOT NULL DEFAULT false,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO yt_runtime_controls(singleton) VALUES (true) ON CONFLICT (singleton) DO NOTHING;

CREATE INDEX IF NOT EXISTS yt_jobs_status_idx ON yt_publishing_jobs(status, scheduled_for);
CREATE INDEX IF NOT EXISTS yt_topics_channel_score_idx ON yt_topics(channel_id, score DESC);
CREATE INDEX IF NOT EXISTS yt_analytics_video_time_idx ON yt_analytics(video_id, observed_at DESC);
