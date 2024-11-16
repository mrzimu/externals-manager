import subprocess
from pathlib import Path
from abc import abstractmethod

from core import BasePackage, BuildConfig


class BesGeant4(BasePackage):
    def __init__(self, build_config: BuildConfig, pre_env_cmds: list[str] = []) -> None:
        super().__init__(build_config, pre_env_cmds)

        self.data_dir = (build_config.install_dir / 'share' / 'Geant4-data' / self.version).resolve()

    @property
    @abstractmethod
    def url(self) -> str:
        ...

    @property
    def name(self) -> str:
        return 'BesGeant4'

    @property
    def build_steps(self) -> list[tuple[str, callable]]:
        """
        Override the default build steps
        """
        return [
            ('download', self.download),
            ('patch', self.patch),
            (f'{self.config_alias}-configure', self.configure),
            (f'{self.config_alias}-build', self.build),
            (f'{self.config_alias}-install', self.install),
            (f'{self.config_alias}-prepare_data', self.prepare_data),
        ]

    def download(self) -> list[str]:
        cmds: list[str] = []

        # Remove existing source directory
        if self.source_dir.exists():
            cmds.append(f'rm -rvf {self.source_dir}')
        else:
            cmds.append(f'mkdir -vp {self.source_dir}')

        # Download source code archive
        src_fpath = (self.build_dir / Path(self.url).name).resolve()
        cmds.append(self.wget_file(self.url, src_fpath))

        # Extract source code archive
        cmds.append(f'tar -xvf {src_fpath} -C {self.source_dir} --strip-components=1')

        return cmds

    def patch(self) -> list[str]:
        patch_file = f'{self.patch_dir}/{self.name}-{self.version}.patch'

        # Test if the patch file have been applied
        proc = subprocess.run(['patch', '-p1', '-N', '--dry-run', '-i', str(patch_file), '-d', str(self.source_dir)])
        if proc.returncode != 0:
            return []
        else:
            return [f'patch -p1 -N -i {patch_file} -d {self.source_dir}']

    def configure(self) -> list[str]:
        cmake_args = self.gen_cmake_args(
            {
                "CMAKE_BUILD_TYPE": self.build_config.cmake_build_type,
                "CMAKE_INSTALL_PREFIX": self.install_dir,
                "GEANT4_INSTALL_DATA": 'OFF' if self.data_dir.exists() else 'ON',
                "GEANT4_USE_GDML": 'ON',
                "GEANT4_USE_SYSTEM_CLHEP": 'ON'
            }
        )
        return [f'cmake -B {self.build_dir} -S {self.source_dir} {cmake_args}']

    def build(self) -> list[str]:
        return [f'cmake --build {self.build_dir} --target install -- -j{self.build_config.n_proc}']

    def install(self) -> list[str]:
        return []

    def prepare_data(self) -> list[str]:
        local_data_dir = f'{self.install_dir}/share/Geant4-{self.version[1:]}/data'

        if self.data_dir.exists():
            return [f'ln -sv {self.data_dir} {local_data_dir}']

        else:
            return [
                f'mkdir -vp {self.data_dir}',
                f'mv -v {local_data_dir} {self.data_dir}',
                f'ln -sv {self.data_dir} {local_data_dir}'
            ]

    def setup_cmds(self) -> dict[str, list[str]]:
        sh_cmds = [f'source {self.install_dir}/bin/geant4.sh']

        csh_cmds = [f'source {self.install_dir}/bin/geant4.csh {self.install_dir}/bin']

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class BesGeant4_10_7_2(BesGeant4):
    @property
    def version(self) -> str:
        return 'v10.7.2'

    @property
    def url(self) -> str:
        return "https://gitlab.cern.ch/geant4/geant4/-/archive/v10.7.2/geant4-v10.7.2.tar.gz"
