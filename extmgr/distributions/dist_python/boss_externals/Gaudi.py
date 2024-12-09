from abc import abstractmethod
from extmgr import BasePackage, CmdList


class Gaudi(BasePackage):
    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def git_tag(self) -> str:
        raise NotImplementedError

    @property
    def git_url(self) -> str:
        return 'https://gitlab.cern.ch/gaudi/Gaudi.git'

    @property
    def name(self) -> str:
        return 'Gaudi'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        clone_cmds = self.clone_git_repo(self.git_url, self.git_tag)

        patch_file = self.patch_dir / f'{self.name}-{self.version}.patch'
        patch_cmds = self.apply_patch(patch_file)

        return [
            ('clone', clone_cmds),
            # ('patch', patch_cmds)
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        config_cmds = self.cmake_config({'GAUDI_ENABLE_GAUDIALG': 'ON'})
        build_cmds = self.cmake_build()

        return [
            ('config', config_cmds),
            ('build', build_cmds)
        ]

    def setup_cmds(self) -> dict[str, list[str]]:
        env_to_append = [("INCLUDE", f"{self.install_dir}/include"),
                         ("LIB", f"{self.install_dir}/lib64"),
                         ("PATH", f"{self.install_dir}/bin"),
                         ("LD_LIBRARY_PATH", f"{self.install_dir}/lib64"),
                         ("PYTHONPATH", f"{self.install_dir}/python")]

        sh_cmds = self.append_envvar(env_to_append, 'sh')
        csh_cmds = self.append_envvar(env_to_append, 'csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class Gaudi_v38r2(Gaudi):
    @property
    def version(self) -> str: return 'v38r2'

    @property
    def git_tag(self) -> str: return 'v38r2'
