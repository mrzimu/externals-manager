from abc import abstractmethod
from pathlib import Path
from extmgr import BasePackage, BuildConfig, CmdList


class BesGeant4(BasePackage):
    def __init__(self) -> None:
        super().__init__()

        # Geant4 Data
        self.data_dir: Path = None

    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def url(self) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return 'BesGeant4'

    def set_config(self, config: BuildConfig) -> None:
        """
        Reimplement the set_config method to set the data_dir
        """
        super().set_config(config)
        self.data_dir = (config.install_prefix / 'share' / 'Geant4-data' / self.version).resolve()

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        archive_file = self.build_dir / Path(self.url).name

        download_cmds = self.download_file(self.url, archive_file)
        extract_cmds = self.extract_archive_to_source(archive_file)

        patch_file = self.patch_dir / f'{self.name}-{self.version}.patch'
        patch_cmds = self.apply_patch(patch_file)

        return [
            ('download', download_cmds),
            ('extract', extract_cmds),
            ('patch', patch_cmds)
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        cmake_args = {
            "GEANT4_INSTALL_DATA": 'OFF' if self.data_dir.exists() else 'ON',
            "GEANT4_USE_GDML": 'ON',
            "GEANT4_USE_SYSTEM_CLHEP": 'ON'
        }

        config_cmds = self.cmake_config(cmake_args)
        build_cmds = self.cmake_build()

        # prepare data
        private_data_dir = self.install_dir / 'share' / f'Geant4-{self.version[1:]}' / 'data'
        prepare_data_cmds = [
            f'if [ -d {self.data_dir} ]; then',
            f'    ln -sv {self.data_dir} {private_data_dir}',
            f'else',
            f'    mkdir -vp {self.data_dir.parent}',
            f'    mv -v {private_data_dir} {self.data_dir}',
            f'    ln -sv {self.data_dir} {private_data_dir}',
            f'fi'
        ]

        return [
            ('config', config_cmds),
            ('build', build_cmds),
            ('prepare_data', prepare_data_cmds)
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
