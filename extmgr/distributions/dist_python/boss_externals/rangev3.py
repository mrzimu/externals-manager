from abc import abstractmethod
from pathlib import Path
from extmgr import BasePackage, CmdList


class rangev3(BasePackage):
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
        return 'rangev3'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        archive_file = self.build_dir / Path(self.url).name

        download_cmds = self.download_file(self.url, archive_file)
        extract_cmds = self.extract_archive_to_source(archive_file)

        return [
            ('download', download_cmds),
            ('extract', extract_cmds)
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        config_cmds = self.cmake_config({'CMAKE_CXX_FLAGS': '"-Wno-changes-meaning"'})
        build_cmds = self.cmake_build()

        return [
            ('config', config_cmds),
            ('build', build_cmds)
        ]

    def setup_cmds(self) -> dict[str, list[str]]:
        lib_dir = self.install_dir / 'lib64' if (self.install_dir / 'lib64').exists() else self.install_dir / 'lib'
        env_to_append = [("INCLUDE", f"{self.install_dir}/include"),
                         ("LIB", f"{lib_dir}"),
                         ("CMAKE_PREFIX_PATH", f"{lib_dir}/cmake/range-v3")]

        sh_cmds = self.append_envvar(env_to_append, 'sh')
        csh_cmds = self.append_envvar(env_to_append, 'csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class rangev3_0_11_0(rangev3):
    @property
    def version(self) -> str:
        return '0.11.0'

    @property
    def url(self) -> str:
        return 'https://lcgpackages.web.cern.ch/tarFiles/sources/rangev3-0.11.0.tgz'
