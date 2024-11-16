from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class BuildConfig:
    patch_dir: Path
    build_dir: Path
    install_dir: Path

    cmake_build_type: Literal['Release', 'Debug']

    config_alias: str

    n_proc: int = 1
    dry_run: bool = False

    def __str__(self) -> str:
        return self.config_alias
