from abc import abstractmethod
from pathlib import Path
from collections import defaultdict
import json
from extmgr import UniquePackage, CmdList, BuildConfig


class Boost(UniquePackage):
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
        return 'Boost'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        archive_file = self.build_dir / Path(self.url).name

        download_cmds = self.download_file(self.url, archive_file)
        extract_cmds = self.extract_archive_to_source(archive_file)

        # for Boost, build and install are also common
        build_cmds = [
            f'cd {self.source_dir}',
            f'./bootstrap.sh --prefix={self.install_dir} --with-python=python3',
        ]

        install_cmds = [
            f'cd {self.source_dir}',
            f'./b2 install',
        ]

        return [
            ('download', download_cmds),
            ('extract', extract_cmds),
            ('build', build_cmds),
            ('install', install_cmds)
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        return []

    def setup_cmds(self) -> dict[str, list[str]]:
        env_to_append = [("INCLUDE", f"{self.install_dir}/include"),
                         ("LIB", f"{self.install_dir}/lib"),
                         ("LD_LIBRARY_PATH", f"{self.install_dir}/lib"),
                         ("CMAKE_PREFIX_PATH", f"{self.install_dir}/lib/cmake/Boost-{self.version}")]

        sh_cmds = self.append_envvar(env_to_append, 'sh')
        csh_cmds = self.append_envvar(env_to_append, 'csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class Boost_1_85_0(Boost):
    @property
    def version(self) -> str:
        return '1.85.0'

    @property
    def url(self) -> str:
        return 'https://lcgpackages.web.cern.ch/tarFiles/sources/boost_1_85_0.tar.gz'
