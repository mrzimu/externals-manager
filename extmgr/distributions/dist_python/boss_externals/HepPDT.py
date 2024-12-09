from abc import abstractmethod
from pathlib import Path
from extmgr import UniquePackage, CmdList


class HepPDT(UniquePackage):
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
        return 'HepPDT'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        archive_file = self.build_dir / Path(self.url).name

        download_cmds = self.download_file(self.url, archive_file)
        extract_cmds = self.extract_archive_to_source(archive_file)

        config_cmds = [
            f'cd {self.source_dir}',
            f'./configure --prefix={self.install_dir}',
            f'cd -'
        ]

        build_cmds = [
            f'cd {self.source_dir}',
            f'make install -j{self.build_config.n_jobs}',
            f'cd -'
        ]

        return [
            ('download', download_cmds),
            ('extract', extract_cmds),
            ('config', config_cmds),
            ('build', build_cmds)
        ]

    def setup_cmds(self) -> dict[str, list[str]]:
        env_to_append = [("INCLUDE", f"{self.install_dir}/include"),
                         ("LIB", f"{self.install_dir}/lib"),
                         ("LD_LIBRARY_PATH", f"{self.install_dir}/lib")]

        sh_cmds = self.append_envvar(env_to_append, 'sh')
        csh_cmds = self.append_envvar(env_to_append, 'csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class HepPDT_2_06_01(HepPDT):
    @property
    def version(self) -> str:
        return '2.06.01'

    @property
    def url(self) -> str:
        return 'https://lcgpackages.web.cern.ch/tarFiles/sources/HepPDT-2.06.01.tar.gz'
