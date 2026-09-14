"""Environment-backed configuration with safe defaults."""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ChannelConfig:
    name: str
    niche: str
    content_type: str = "educational documentary"
    language: str = "en"
    audience: str = "18-45"
    video_min_minutes: int = 8
    video_max_minutes: int = 12
    upload_frequency: str = "1/day"
    style: str = "cinematic documentary"
    narrator: str = "documentary"
    auto_publish: bool = False
    max_reused_content_risk: float = 35.0
    min_originality_score: float = 65.0

    @classmethod
    def from_env(cls) -> "ChannelConfig":
        return cls(
            name=os.getenv("YT_CHANNEL_NAME", "My Channel"),
            niche=os.getenv("YT_CHANNEL_NICHE", "science"),
            content_type=os.getenv("YT_CONTENT_TYPE", "educational documentary"),
            language=os.getenv("YT_LANGUAGE", "en"),
            audience=os.getenv("YT_AUDIENCE", "18-45"),
            video_min_minutes=int(os.getenv("YT_VIDEO_MIN_MINUTES", "8")),
            video_max_minutes=int(os.getenv("YT_VIDEO_MAX_MINUTES", "12")),
            upload_frequency=os.getenv("YT_UPLOAD_FREQUENCY", "1/day"),
            style=os.getenv("YT_STYLE", "cinematic documentary"),
            narrator=os.getenv("YT_NARRATOR", "documentary"),
            auto_publish=os.getenv("YT_AUTO_PUBLISH", "false").lower() == "true",
            max_reused_content_risk=float(os.getenv("YT_MAX_REUSED_RISK", "35")),
            min_originality_score=float(os.getenv("YT_MIN_ORIGINALITY", "65")),
        )


@dataclass(frozen=True)
class RuntimeConfig:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/yt_autopilot")
    storage_bucket: str = os.getenv("S3_BUCKET", "yt-autopilot")
    storage_endpoint: str = os.getenv("S3_ENDPOINT", "")
    ffmpeg_bin: str = os.getenv("FFMPEG_BIN", "ffmpeg")
    ffprobe_bin: str = os.getenv("FFPROBE_BIN", "ffprobe")
    max_daily_budget: float = float(os.getenv("MAX_DAILY_BUDGET", "20"))
    max_video_cost: float = float(os.getenv("MAX_VIDEO_COST", "5"))
