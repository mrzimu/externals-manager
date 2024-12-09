from abc import abstractmethod
from extmgr import BasePackage, CmdList


class Fmt(BasePackage):
    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str: return 'fmt'

    @property
    def git_url(self) -> str: return 'https://github.com/fmtlib/fmt.git'

    @property
    def git_tag(self) -> str: return self.version

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        clone_cmds = self.clone_git_repo(self.git_url, self.git_tag)
        return [
            ('clone', clone_cmds)
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        config_cmds = self.cmake_config({'BUILD_SHARED_LIBS': 'TRUE'})
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
            ("CMAKE_PREFIX_PATH", f"{self.install_dir}/lib64/cmake/fmt")
        ]

        sh_cmds = self.append_envvar(env_to_append, shell='sh')
        csh_cmds = self.append_envvar(env_to_append, shell='csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class Fmt_10_2_1(Fmt):
    @property
    def version(self) -> str: return '10.2.1'


class Fmt_11_0_2(Fmt):
    @property
    def version(self) -> str: return '11.0.2'

    @property
    def git_tag(self) -> str: return '11.0.2'  # you can override the git_tag property if needed
