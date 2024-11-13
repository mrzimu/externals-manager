import json
import time
import subprocess
from typing import Union
from collections import defaultdict
from logging import getLogger
from abc import ABC, abstractmethod

from .BuildConfig import BuildConfig

class BasePackage(ABC):
    def __init__(self,
                 build_config: BuildConfig,
                 pre_env_cmds: list[str] = []) -> None:
        super().__init__()

        self.logger = getLogger(self.__class__.__name__)
        self.build_config = build_config
        self.pre_env_cmds = [i for i in pre_env_cmds if not i.startswith('#')]

        # set necessarry directories path
        self.patch_dir = build_config.patch_dir.resolve()
        self.build_dir = (build_config.build_dir / self.name / self.version / self.build_config.config_alias).resolve()
        self.install_dir = (build_config.install_dir / self.name / self.version / self.build_config.config_alias).resolve()
        self.source_dir = (build_config.install_dir / self.name / self.version / 'src').resolve()
        self.step_stamp_path = (build_config.install_dir / self.name / self.version / 'step_stamp.json').resolve()
        self.config_alias = build_config.config_alias

        self.info(f'      Source: {self.source_dir}')
        self.info(f'       Patch: {self.patch_dir}')
        self.info(f'       Build: {self.build_dir}')
        self.info(f'     Install: {self.install_dir}')
        self.info(f'  Step Stamp: {self.step_stamp_path}')
        self.info(f'Config Alias: {self.config_alias}')

        # Try to load step stamp file
        self.step_stamp = defaultdict(int)
        if self.step_stamp_path.exists():
            try:
                with open(self.step_stamp_path) as f:
                    self.step_stamp.update(json.load(f))
            except Exception as e:
                self.error(f'Failed to load step stamp file: {e}, please check it manually or remove it!')
                raise RuntimeError('Failed to load step stamp file')

    @abstractmethod
    def download(self) -> list[str]: ...

    @abstractmethod
    def patch(self) -> list[str]: ...

    @abstractmethod
    def configure(self) -> list[str]: ...

    @abstractmethod
    def build(self) -> list[str]: ...

    @abstractmethod
    def install(self) -> list[str]: ...

    @abstractmethod
    def setup_cmds(self) -> dict[str, list[str]]:
        """
        Return `{shell: setup_cmd}` dictionary where `shell` is the shell type 
        and `setup_cmd` is the list of commands to be executed
        """
        ...

    @property
    def build_steps(self) -> dict[str, list[str]]:
        return {
            'download': self.download(),
            'patch': self.patch(),
            f'{self.config_alias}-configure': self.configure(),
            f'{self.config_alias}-build': self.build(),
            f'{self.config_alias}-install': self.install(),
        }

    def _make(self) -> bool:
        # Create directories
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.install_dir.parent.mkdir(parents=True, exist_ok=True)

        while True:
            step = self._get_next_step()
            if step is None:
                self.info('All steps are completed')
                return True

            cmds = self.build_steps[step]
            if not cmds:
                self.step_stamp[step] = time.time_ns()
                self._save_step_stamp()
                self.info(f'Step skipped: {step}')
                continue

            cmds = self.pre_env_cmds + cmds
            cmds_str = ' && '.join(cmds)

            self.info(f'Running step: {step}')

            try:
                res = subprocess.run(cmds_str, shell=True, cwd=self.build_dir)

                if res.returncode == 0:
                    self.step_stamp[step] = time.time_ns()
                    self._save_step_stamp()
                    self.info(f'Step completed: {step}')
                else:
                    self.error(f'Failed to run step: {step}')
                    return False

            except KeyboardInterrupt:
                self.warning('Interrupted by user')
                return False

    def _get_next_step(self) -> Union[str, None]:
        steps = list(self.build_steps.keys())

        for i, step in enumerate(steps[:-1]):
            if self.step_stamp[step] == 0:
                return step

            next_step = steps[i + 1]
            if self.step_stamp[step] > self.step_stamp[next_step]:
                return next_step

        last_step = steps[-1]
        if self.step_stamp[last_step] == 0:
            return last_step

        return None

    def _save_step_stamp(self):
        with open(self.step_stamp_path, 'w') as f:
            json.dump(self.step_stamp, f, indent=4)

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def fatal(self, msg: str) -> None:
        self.logger.fatal(msg)

    def gen_cmake_args(self, args: dict[str, str]) -> str:
        cmd = ' '.join([f'-D{k}={v} ' for k, v in args.items()])
        return cmd.strip()
