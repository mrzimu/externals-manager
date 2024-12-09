from abc import abstractmethod
from pathlib import Path
from extmgr import BasePackage, CmdList


class AIDA(BasePackage):
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
        return 'AIDA'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        archive_file = self.build_dir / Path(self.url).name

        download_cmds = self.download_file(self.url, archive_file)
        extract_cmds = self.extract_archive_to_source(archive_file)

        return [
            ('download', download_cmds),
            ('extract', extract_cmds),
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        install_cmds = [f'cp -r {self.source_dir}/cpp {self.install_dir}']
        return [('install', install_cmds)]

    def setup_cmds(self) -> dict[str, list[str]]:
        env_to_append = [("INCLUDE", f"{self.install_dir}/cpp")]

        sh_cmds = self.append_envvar(env_to_append, 'sh')
        csh_cmds = self.append_envvar(env_to_append, 'csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class AIDA_3_2_1(AIDA):
    @property
    def version(self) -> str:
        return '3.2.1'

    @property
    def url(self) -> str:
        return 'https://lcgpackages.web.cern.ch/tarFiles/sources/aida-3.2.1-src.tar.gz'
