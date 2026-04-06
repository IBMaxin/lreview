"""Config loader for lreview."""
import tomllib
from pathlib import Path
from dataclasses import dataclass, field


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "lreview" / "config.toml"
FALLBACK_CONFIG_PATH = Path(__file__).parent.parent / "config.default.toml"


@dataclass
class ModelConfig:
    review_model: str = "gemma4:e2b"
    patch_model: str = "qwen3.5:4b"


@dataclass
class LimitsConfig:
    max_diff_tokens: int = 3000
    review_timeout: int = 60
    temperature: float = 0.2


@dataclass
class GitConfig:
    default_diff_base: str = "HEAD~1"


@dataclass
class Config:
    models: ModelConfig = field(default_factory=ModelConfig)
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    git: GitConfig = field(default_factory=GitConfig)


def load_config(path: Path | None = None) -> Config:
    """Load config from TOML file, falling back to defaults.

    Args:
        path: Optional explicit path to config.toml.

    Returns:
        Populated Config dataclass.
    """
    cfg_path = path or DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        cfg_path = FALLBACK_CONFIG_PATH
    if not cfg_path.exists():
        return Config()

    with open(cfg_path, "rb") as f:
        raw = tomllib.load(f)

    return Config(
        models=ModelConfig(**raw.get("models", {})),
        limits=LimitsConfig(**raw.get("limits", {})),
        git=GitConfig(**raw.get("git", {})),
    )
