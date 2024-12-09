from abc import abstractmethod
from extmgr import BasePackage, CmdList


class Catch2(BasePackage):
    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @property
    def git_tag(self) -> str: return self.version

    @property
    def name(self) -> str: return 'Catch2'

    @property
    def git_url(self) -> str: return 'https://github.com/catchorg/Catch2.git'

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
        env_to_append: list[tuple[str, str]] = [
            ("INCLUDE", f"{self.install_dir}/include"),
            ("LIB", f"{self.install_dir}/lib64"),
            ("LD_LIBRARY_PATH", f"{self.install_dir}/lib64"),
            ("CMAKE_PREFIX_PATH", f"{self.install_dir}/lib64/cmake/Catch2")
        ]

        sh_cmds = self.append_envvar(env_to_append, shell='sh')
        csh_cmds = self.append_envvar(env_to_append, shell='csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class Catch2_v3_7_1(Catch2):
    @property
    def version(self) -> str: return 'v3.7.1'


class Catch2_v3_5_4(Catch2):
    @property
    def version(self) -> str: return 'v3.5.4'
