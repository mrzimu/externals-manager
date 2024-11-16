import json
import time
import os
import subprocess
from typing import Union, Literal
from collections import defaultdict
from logging import getLogger
from abc import ABC, abstractmethod

from .BuildConfig import BuildConfig


class BasePackage(ABC):
    def __init__(self,
                 build_config: BuildConfig,
                 pre_env_cmds: list[str] = None) -> None:
        super().__init__()

        if pre_env_cmds is None:
            pre_env_cmds = []

        self.logger = getLogger(f'{self.name}-{self.version}')
        self.build_config = build_config
        self.pre_env_cmds = [i for i in pre_env_cmds if not i.startswith('#')]

        # set necessary directories path
        self.patch_dir = build_config.patch_dir.resolve()
        self.build_dir = (build_config.build_dir / self.name / self.version / self.build_config.config_alias).resolve()
        self.install_dir = (build_config.install_dir / self.name / self.version /
                            self.build_config.config_alias).resolve()
        self.source_dir = (build_config.install_dir / self.name / self.version / 'src').resolve()
        self.step_stamp_path = (build_config.install_dir / self.name / self.version / 'step_stamp.json').resolve()
        self.config_alias = build_config.config_alias

        self.info(f'---> {self.name}-{self.version}')
        self.info(f'Source: {self.source_dir}')
        self.info(f'Patch: {self.patch_dir}')
        self.info(f'Build: {self.build_dir}')
        self.info(f'Install: {self.install_dir}')
        self.info(f'Step Stamp: {self.step_stamp_path}')
        self.info(f'Config Alias: {self.config_alias}')
        self.info('')

        # Try to load step stamp file
        self.step_stamp = defaultdict(int)
        if self.step_stamp_path.exists():
            try:
                with open(self.step_stamp_path) as f:
                    self.step_stamp.update(json.load(f))
            except Exception as e:
                self.error(f'Failed to load step stamp file: {e}, please check it manually or remove it!')
                raise RuntimeError('Failed to load step stamp file')

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        ...

    @abstractmethod
    def download(self) -> list[str]:
        ...

    @abstractmethod
    def patch(self) -> list[str]:
        ...

    @abstractmethod
    def configure(self) -> list[str]:
        ...

    @abstractmethod
    def build(self) -> list[str]:
        ...

    @abstractmethod
    def install(self) -> list[str]:
        ...

    @abstractmethod
    def setup_cmds(self) -> dict[str, list[str]]:
        """
        Return `{shell: setup_cmd}` dictionary where `shell` is the shell type 
        and `setup_cmd` is the list of commands to be executed
        """
        ...

    @property
    def build_steps(self) -> list[tuple[str, callable]]:
        return [
            ('download', self.download),
            ('patch', self.patch),
            (f'{self.config_alias}-configure', self.configure),
            (f'{self.config_alias}-build', self.build),
            (f'{self.config_alias}-install', self.install),
        ]

    def _make(self) -> bool:
        # Create directories
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.install_dir.parent.mkdir(parents=True, exist_ok=True)

        start_index = self._get_start_step_index()
        if start_index is None:
            self.info('All steps are completed')
            return True

        if self.build_config.dry_run:
            self.fatal(f"---------> {self.name}-{self.version}")

        for i in range(start_index, len(self.build_steps)):
            step, step_func = self.build_steps[i]
            cmds = step_func()

            # add environment setup commands
            cmds = self.pre_env_cmds + cmds

            # dry run
            if self.build_config.dry_run:
                self.fatal(f'Commands of "{step}":')
                for cmd in cmds:
                    self.fatal(f'- {cmd}')
                self.fatal('')
                continue

            # save the commands to a shell script
            tmp_script_path = self.build_dir / f'{step}.sh'
            open(tmp_script_path, 'w').write('\n'.join(cmds))

            # run the commands
            try:
                proc = subprocess.run(['bash', f'{step}.sh'], cwd=self.build_dir)
            except KeyboardInterrupt:
                self.warning('Interrupted by user')
                return False

            if proc.returncode != 0:
                self.error(f'Failed to run step: {step}')
                return False
            else:
                self.step_stamp[step] = time.time_ns()
                self._save_step_stamp()
                os.remove(tmp_script_path)
                self.info(f'Step completed: {step}')

        if self.build_config.dry_run:
            self.fatal(f"{self.name}-{self.version} <---------\n")

        return True

    def _get_start_step_index(self) -> Union[int, None]:
        """
        Return the index of the first step that has not been completed,
        None if all steps are completed.
        """
        steps = [step for step, _ in self.build_steps]

        for i, step in enumerate(steps[:-1]):
            if self.step_stamp[step] == 0:
                return i

            next_step = steps[i + 1]
            if self.step_stamp[step] > self.step_stamp[next_step]:
                return i + 1

        last_step = steps[-1]
        if self.step_stamp[last_step] == 0:
            return len(steps) - 1

        return None

    def _save_step_stamp(self):
        with open(self.step_stamp_path, 'w') as f:
            json.dump(self.step_stamp, f, indent=4)

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

    def clone_git_repo(self, url: str, branch: str) -> str:
        return f'git clone {url} {self.source_dir} --branch {branch}'

    @staticmethod
    def wget_file(url: str, file: str) -> str:
        return f'wget {url} -O {file}'

    @staticmethod
    def gen_cmake_args(args: dict[str, str]) -> str:
        cmd = ' '.join([f'-D{k}={v} ' for k, v in args.items()])
        return cmd.strip()

    @staticmethod
    def append_envvar(key_value_paris: list[tuple[str, str]], shell: Literal['sh', 'csh']) -> list[str]:
        res = []

        for k, v in key_value_paris:
            if shell == 'sh':
                res += [
                    'if [ -z "$%s" ]; then' % k,
                    '    export %s="%s"' % (k, v),
                    'else',
                    '    export %s="%s:$%s"' % (k, v, k),
                    'fi',
                    ''
                ]

            elif shell == 'csh':
                res += [
                    'if ( $?%s ) then' % k,
                    '    setenv %s "%s:$%s"' % (k, v, k),
                    'else',
                    '    setenv %s "%s"' % (k, v),
                    'endif',
                    ''
                ]

            else:
                raise ValueError('Invalid shell type')

        return res
