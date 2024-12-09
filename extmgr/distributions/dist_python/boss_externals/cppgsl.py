from abc import abstractmethod
from pathlib import Path
from extmgr import BasePackage, CmdList


class cppgsl(BasePackage):
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
        return 'cppgsl'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        archive_file = self.build_dir / Path(self.url).name

        download_cmds = self.download_file(self.url, archive_file)
        extract_cmds = self.extract_archive_to_source(archive_file)

        return [
            ('download', download_cmds),
            ('extract', extract_cmds)
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        config_cmds = self.cmake_config({
            'CMAKE_CXX_FLAGS': '"-Wno-error=maybe-uninitialized"',
            'GSL_TEST': 'OFF'
        })
        build_cmds = self.cmake_build()

        return [
            ('config', config_cmds),
            ('build', build_cmds)
        ]

    def setup_cmds(self) -> dict[str, list[str]]:
        env_to_append = [("INCLUDE", f"{self.install_dir}/include"),
                         ("CMAKE_PREFIX_PATH", f"{self.install_dir}/share/cmake/Microsoft.GSL")]

        sh_cmds = self.append_envvar(env_to_append, 'sh')
        csh_cmds = self.append_envvar(env_to_append, 'csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class cppgsl_3_1_0(cppgsl):
    @property
    def version(self) -> str:
        return '3.1.0'

    @property
    def url(self) -> str:
        return 'https://lcgpackages.web.cern.ch/tarFiles/sources/cppgsl-3.1.0.tar.gz'
