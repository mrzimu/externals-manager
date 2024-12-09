from abc import ABC, abstractmethod
from pathlib import Path
from collections import deque, defaultdict
import subprocess
import sys
import time
import json
from typing import Literal

from .BuildConfig import BuildConfig
from .ILog import ILog

StepName = str
CmdList = list[str]


class BasePackage(ABC, ILog):
    def __init__(self) -> None:
        ABC.__init__(self)
        ILog.__init__(self)

        self.build_config: BuildConfig = None

        # Common directories for all packages
        self.external_prefix: Path = None  # External prefix directory
        self.patch_dir: Path = None  # Patch directory

        # Build flag, e.g. x86_64-el9-gcc13-opt
        self.build_flag: str = None

        # Package's private directories
        self.pkg_base_dir: Path = None  # Base directory
        self.version_dir: Path = None  # Version directory
        self.source_dir: Path = None  # Source directory
        self.build_dir: Path = None  # Build directory
        self.install_dir: Path = None  # Install directory
        self.stamp_path: Path = None  # Stamp file path

        # Step timestamps, {StepName: Time Stamp}, e.g. {'download': 1234567890, 'patch': 1234567890, ...}
        self.step_stamp: dict[StepName, float] = defaultdict(float)
        self.tmp_bash_path: Path = None  # Temporary bash file path

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the package name

        Returns:
            str: Package name
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Return the package version

        Returns:
            str: Package version
        """
        raise NotImplementedError

    @abstractmethod
    def prepare_src_steps(self) -> list[tuple[StepName, CmdList]]:
        """
        Return a list of `(step_name, step_commands)` tuples. The `step_name` will be used as the
        key in the `build_stamp` file to store the step's timestamp. The `step_commands` should
        be a list of bash commands to be executed.

        You should use this method to prepare the source code for building. This could include
        downloading the source code, extracting it, patching it, etc.

        Returns:
            list[tuple[StepName, CmdList]]: List of `(step_name, [step_commands])` tuples
        """
        raise NotImplementedError

    @abstractmethod
    def build_steps(self) -> list[tuple[StepName, CmdList]]:
        """
        Return a list of `(step_name, step_commands)` tuples. The `step_name` will be used as the
        key in the `build_stamp` file to store the step's timestamp. The `step_commands` should
        be a list of bash commands to be executed.

        You should use this method to build and install the package. This could include running
        `configure`, `make`, `make install`, etc.

        Returns:
            list[tuple[StepName, CmdList]]: List of `(step_name, [step_commands])` tuples
        """
        raise NotImplementedError

    @abstractmethod
    def setup_cmds(self) -> dict[str, CmdList]:
        """
        Return `{shell_type: setup_cmd}` dictionary where `shell_type` is the type of shell
        (`sh`, `csh`, ...) and `setup_cmd` is the list of commands to be executed
        in that shell.

        You should use this method to set up the environment variables, paths, etc. needed to
        use the package.

        Returns:
            dict[str, CmdList]: `{shell_type: setup_cmd}` dictionary
        """
        raise NotImplementedError

    ################################################################
    ####################### Magic functions ########################
    ################################################################
    def __repr__(self) -> str:
        return 'Package(%s %s)' % (self.name, self.version)

    ################################################################
    ####################### Public functions #######################
    ################################################################

    def set_config(self, config: BuildConfig) -> None:
        """
        Set the build configuration for the package

        Args:
            config (BuildConfig): The build configuration object
        """
        self.build_config = config

        self.external_prefix = config.install_prefix.resolve()
        self.patch_dir = config.patch_dir.resolve()

        self.build_flag = config.build_flag

        self.pkg_base_dir = self.external_prefix / self.name
        self.version_dir = self.pkg_base_dir / self.version
        self.source_dir = self.version_dir / 'src'
        self.install_dir = self.version_dir / self.build_flag
        self.stamp_path = self.version_dir / f'step_stamp.json'

        self.build_dir = config.build_prefix / self.name / self.version / self.build_flag
        self.tmp_bash_path = self.build_dir / f'tmp-{self.build_flag}.sh'

        self.debug(f'Base directory: {self.pkg_base_dir}')
        self.debug(f'Source directory: {self.source_dir}')
        self.debug(f'Build directory: {self.build_dir}')
        self.debug(f'Install directory: {self.install_dir}')
        self.debug(f'Stamp file: {self.stamp_path}')
        self.debug(f'Build flag: {self.build_flag}')

        # Try to load stamp file
        if self.stamp_path.exists():
            try:
                with open(self.stamp_path, 'r') as f:
                    tmp_dict = json.load(f)
                    self.step_stamp = defaultdict(int)
                    for k, v in tmp_dict.items():
                        self.step_stamp[k] = v
            except Exception as e:
                self.error(f'Failed to load stamp file: {e}, please check it or remove it!')
                raise RuntimeError('Failed to load stamp file')

    def prepare_directories(self) -> None:
        """
        Prepare the directories for the package. This includes creating the directories
        and setting the paths for the package's private directories.

        Returns:
            None
        """
        dirs_to_make = [
            self.pkg_base_dir,
            self.version_dir,
            self.source_dir,
            self.build_dir,
            self.install_dir
        ]

        for d in dirs_to_make:
            if self.build_config.dry_run:
                self.info(f"Going to make {d}")
            else:
                d.mkdir(parents=True, exist_ok=True)

    def _make(self, env_setup_cmds: CmdList) -> bool:
        """
        Make the package

        Returns:
            bool: True if the package was made successfully, False otherwise.
        """
        self.info(f'Making package {self.name} {self.version}')

        self.info("Preparing directories")
        try:
            self.prepare_directories()
        except Exception as e:
            self.error(f'Failed to make directories: {e}')
            return False

        self.info(f'Preparing source for package {self.name}')
        if not self._exec_steps(env_setup_cmds, self.prepare_src_steps(), add_flag=False):
            return False

        self.info(f'Building package {self.name}')
        if not self._exec_steps(env_setup_cmds, self.build_steps(), add_flag=True):
            return False

        if not self.build_config.dry_run:
            self.info(f'Examing environment setup commands')
            if not self._run_cmds(self.setup_cmds()['sh']):
                self.error(f'Failed to run environment setup commands')
                return False

        return True

    def _exec_steps(self,
                    env_setup_cmds: CmdList,
                    steps: list[tuple[StepName, CmdList]],
                    add_flag: bool) -> bool:
        """
        Execute a list of steps

        Args:
            steps (list[tuple[StepName, CmdList]]): List of
                `(step_name, step_commands)` tuples

        Returns:
            bool: True if the steps were executed successfully, False otherwise.
        """
        # Add build flag to step names
        if add_flag:
            steps = [(f'{self.build_flag}-{step_name}', cmd_list) for step_name, cmd_list in steps]

        # Determine first step
        start_index = -1
        if len(steps) == 1 and self.step_stamp[steps[0][0]] == 0:
            start_index = 0
        else:
            for i in range(len(steps) - 1):
                cur_step_name = steps[i][0]
                next_step_name = steps[i + 1][0]

                if self.step_stamp[cur_step_name] == 0:
                    start_index = i
                    break

                if self.step_stamp[cur_step_name] > self.step_stamp[next_step_name]:
                    start_index = i + 1
                    break

                self.info(f'Step {cur_step_name} is up-to-date')

        if start_index == -1:
            self.info('All steps are up-to-date, skipping')
            return True

        steps = steps[start_index:]

        # Run the steps
        for step_name, cmd_list in steps:
            self.info(f'Running step {step_name}')

            if self.build_config.dry_run:
                self.info(f'Going to execute step {step_name}:')
                self.info('')
                self.info(' $ -----------------------')
                for c in cmd_list:
                    self.info(f' $ {c}')
                self.info(' $ -----------------------')
                self.info('')

            else:
                # Run the commands
                if not self._run_cmds(env_setup_cmds + cmd_list):
                    self.error(f'Failed to run step {step_name}')
                    return False
                else:
                    self.step_stamp[step_name] = time.time()
                    self.save_stamp()

        return True

    def _run_cmds(self, cmd_list: CmdList) -> bool:
        """
        Execute a list of bash commands.

        Args:
            cmd_list (CmdList): The list of bash commands to be executed.
        """
        # Write the bash commands to a file
        try:
            cmd_text = 'set -e\n' + '\n'.join(cmd_list)
            self.tmp_bash_path.write_text(cmd_text)
            self.tmp_bash_path.chmod(0o755)  # Make the file executable
        except Exception as e:
            self.error(f'Failed to write bash commands to file: {e}')
            return False

        # Run the bash file
        try:
            # proc = subprocess.Popen(['bash', str(self.tmp_bash_path)],
            #                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # self.watch_proc(proc)
            proc = subprocess.run(['bash', str(self.tmp_bash_path)])
            if proc.returncode != 0:
                return False
            return True

        except Exception as e:
            self.error(f'Failed to run bash commands: {e}')
            return False

    def save_stamp(self) -> None:
        """
        Save the step timestamps to the stamp file
        """
        with open(self.stamp_path, 'w') as f:
            json.dump(self.step_stamp, f, indent=4)

    @staticmethod
    def watch_proc(proc: subprocess.Popen, nlines: int = 10) -> None:
        """
        Watch the output of a process

        Args:
            proc (subprocess.Popen): The process to watch
        """
        last_lines = deque(maxlen=nlines)

        while True:
            line = proc.stdout.readline()

            if line:
                last_lines.append(line)

                sys.stdout.write("\033[F" * nlines)  # Move cursor up
                for l in last_lines:
                    print(l)
                sys.stdout.flush()

            if proc.poll() is not None:
                break

            time.sleep(0.1)

    ################################################################
    ####################### Helper functions #######################
    ################################################################

    def apply_patch(self, patch_file: Path) -> CmdList:
        """
        Apply a patch file to the source directory.

        Args:
            patch_file (Path): Path to the patch file.

        Returns:
            CmdList: List of commands to apply the patch file.
        """
        return [
            f'cd {self.source_dir}',
            f'patch -p1 -N --dry-run -i {patch_file}',
            f'if [ $? -eq 0 ]; then',
            f'    patch -p1 -N -i {patch_file}',
            f'fi',
            f'cd -'
        ]

    def clone_git_repo(self, repo_url: str, tag: str, remove_exist: bool = False) -> CmdList:
        """
        Clone a git repository.

        Args:
            repo_url (str): URL of the git repository.
            tag (str): Tag to checkout.
            remove_exist (bool, optional): Whether to remove the existing repository. Defaults to True.

        Returns:
            CmdList: List of commands to clone the git repository.
        """
        res = []
        if remove_exist:
            res += [
                f'if [ -d {self.source_dir} ]; then',
                f'    rm -rvf {self.source_dir}',
                f'fi'
            ]
        res += [f'git clone {repo_url} {self.source_dir}']
        res += [f'cd {self.source_dir}', f'git checkout {tag}', 'cd -']
        return res

    def download_file(self, url: str, dest: Path = None, remove_exist: bool = False) -> CmdList:
        """
        Download a file.

        Args:
            url (str): URL of the file.
            dest (Path, optional): Destination path to save the file. Defaults to None.
            remove_exist (bool, optional): Whether to remove the existing file. Defaults to False.

        Returns:
            CmdList: List of commands to download the file.
        """
        res = []
        try:
            file_path = (self.build_dir / Path(url).name) if dest is None else dest
        except Exception as e:
            self.error(f'Failed to get file path: {e}')
            self.error(f"Check if the URL is valid: {url}")
            raise e

        if remove_exist:
            res += [
                f'if [ -e {file_path} ]; then',
                f'    rm -rvf {file_path}',
                f'fi'
            ]

        res += [f'wget {url} -O {file_path}']

        return res

    def extract_archive(self, archive_path: Path, dest: Path = None, strip_components: int = 1) -> CmdList:
        """
        Extract an archive file.

        Args:
            archive_path (Path): Path to the archive file.
            dest (Path, optional): Destination path to extract the archive file. Defaults to None.
            strip_components (int, optional): Number of leading path components to strip. Defaults to 1.

        Returns:
            CmdList: List of commands to extract the archive file.
        """
        res = []
        dest = self.source_dir if dest is None else dest
        res += [f'tar -xvf {archive_path} -C {dest} --strip-components={strip_components}']
        return res

    def extract_archive_to_source(self, archive_path: Path, strip_components: int = 1) -> CmdList:
        """
        Extract an archive file to the source directory.

        Args:
            archive_path (Path): Path to the archive file.
            strip_components (int, optional): Number of leading path components to strip. Defaults to 1.

        Returns:
            CmdList: List of commands to extract the archive file.
        """
        return self.extract_archive(archive_path, self.source_dir, strip_components)

    def cmake_config(self, cmake_args: dict[str, str] = {}) -> CmdList:
        """
        Generates the CMake configuration command for the package.
        If `CMAKE_BUILD_TYPE` and `CMAKE_INSTALL_PREFIX` are not provided in `cmake_args`,
        they will be set to `self.build_config.cmake_build_type` and `self.install_dir` respectively.

        Args:
            cmake_args (dict[str, str], optional): Additional CMake arguments. Defaults to {}.

        Returns:
            str: The CMake configuration command.
        """
        res = f'cmake -B {self.build_dir} -S {self.source_dir}'

        for key, val in cmake_args.items():
            res += f' -D{key}={val}'

        if 'CMAKE_BUILD_TYPE' not in cmake_args:
            res += f' -DCMAKE_BUILD_TYPE={self.build_config.cmake_build_type}'

        if 'CMAKE_INSTALL_PREFIX' not in cmake_args:
            res += f' -DCMAKE_INSTALL_PREFIX={self.install_dir}'

        return [res]

    def cmake_build(self, target: str = 'install') -> CmdList:
        """
        Generate cmake build commands.

        Args:
            target (str, optional): Target to build. Defaults to 'install'.

        Returns:
            CmdList: List of cmake build commands.
        """
        return [f'cmake --build {self.build_dir} --target {target} -- -j{self.build_config.n_jobs}']

    @staticmethod
    def append_envvar(key_value_paris: list[tuple[str]], shell: Literal['sh', 'csh']) -> CmdList:
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
