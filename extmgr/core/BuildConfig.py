from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class BuildConfig:
    patch_dir: Path
    build_prefix: Path
    install_prefix: Path

    cmake_build_type: Literal['Release', 'Debug', 'RelWithDebInfo']

    build_flag: str

    n_jobs: int = 1
    dry_run: bool = False

    def __str__(self) -> str:
        return self.build_flag
