from collections import defaultdict
import json

from .BuildConfig import BuildConfig
from .BasePackage import BasePackage, CmdList


class UniquePackage(BasePackage):
    """
    UniquePackage is a subclass of BasePackage, which escapes the influence of different build type.
    It has only one install directory and one build directory.
    """

    def set_config(self, config: BuildConfig) -> None:
        """
        Set the build configuration for the package.
        Reimplement this method to make Boost independent to build-flag.

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
        self.install_dir = self.version_dir / 'install'  # unique
        self.stamp_path = self.version_dir / f'step_stamp.json'

        self.build_dir = config.build_prefix / self.name / self.version  # unique
        self.tmp_bash_path = self.build_dir / f'tmp.sh'  # unique

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

    def build_steps(self) -> list[tuple[str, CmdList]]:
        return []
