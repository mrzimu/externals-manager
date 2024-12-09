from abc import abstractmethod
from extmgr import BasePackage, CmdList


class BesGDML(BasePackage):
    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def git_tag(self) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str: return 'BesGDML'

    @property
    def git_url(self) -> str:
        return 'https://code.ihep.ac.cn/boss/boss_external/besgdml.git'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        clone_cmds = self.clone_git_repo(self.git_url, self.git_tag)
        return [
            ('clone', clone_cmds)
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        config_cmds = self.cmake_config()
        build_cmds = self.cmake_build()

        return [
            ('config', config_cmds),
            ('build', build_cmds)
        ]

    def setup_cmds(self) -> dict[str, list[str]]:
        env_to_append = [
            ("PATH", f"{self.install_dir}/include"),
            ("LIB", f"{self.install_dir}/lib64"),
            ("LD_LIBRARY_PATH", f"{self.install_dir}/lib64")
        ]

        sh_cmds = self.append_envvar(env_to_append, shell='sh')
        csh_cmds = self.append_envvar(env_to_append, shell='csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class BesGDML_2_8_1(BesGDML):
    @property
    def version(self) -> str:
        return '2.8.1'

    @property
    def git_tag(self) -> str:
        return '2.8.1'
