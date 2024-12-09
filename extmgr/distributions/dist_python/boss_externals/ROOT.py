from abc import abstractmethod
from pathlib import Path
from extmgr import UniquePackage, CmdList


class ROOT(UniquePackage):
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
        return 'root'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        archive_file = self.build_dir / Path(self.url).name

        download_cmds = self.download_file(self.url, archive_file)
        extract_cmds = self.extract_archive_to_source(archive_file)

        patch_file = self.patch_dir / f'{self.name}-{self.version}.patch'
        patch_cmds = self.apply_patch(patch_file)

        config_cmds = self.cmake_config()
        build_cmds = self.cmake_build()

        return [
            ('download', download_cmds),
            ('extract', extract_cmds),
            ('patch', patch_cmds),
            ('config', config_cmds),
            ('build', build_cmds)
        ]

    def setup_cmds(self) -> dict[str, list[str]]:
        sh_cmds = [f'source {self.install_dir}/bin/thisroot.sh']
        csh_cmds = [f'source {self.install_dir}/bin/thisroot.csh']

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class ROOT_v6_32_02(ROOT):
    @property
    def version(self) -> str:
        return 'v6.32.02'

    @property
    def url(self) -> str:
        return 'https://root.cern/download/root_v6.32.02.source.tar.gz'
