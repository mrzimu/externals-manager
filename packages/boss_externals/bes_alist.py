from abc import abstractmethod
from typing import List, Tuple

from core import BasePackage, BuildConfig


class BesAlist(BasePackage):
    def __init__(self, build_config: BuildConfig, pre_env_cmds=None):
        super().__init__(build_config, pre_env_cmds)

        self.git_repo = 'https://code.ihep.ac.cn/boss8-upgrade/external/besalist.git'
        self.git_tag = 'main'

    @property
    def name(self) -> str: return 'BesAlist'

    @property
    def version(self) -> str: return 'test'

    def download(self) -> list[str]:
        cmds = []
        if self.source_dir.exists():
            cmds += [f'rm -rvf {self.source_dir}']

        cmds += [self.clone_git_repo(self.git_repo, self.git_tag)]
        return cmds

    def patch(self) -> list[str]:
        return []

    def configure(self) -> list[str]:
        cmake_args = self.gen_cmake_args({
            'CMAKE_BUILD_TYPE': self.build_config.cmake_build_type,
            'CMAKE_INSTALL_PREFIX': self.install_dir,
        })
        return [f'cmake -B {self.build_dir} -S {self.source_dir} {cmake_args}']

    def build(self) -> list[str]:
        return [f'cmake --build {self.build_dir} --target install -- -j{self.build_config.n_proc}']

    def install(self) -> list[str]:
        return []

    def setup_cmds(self) -> dict[str, list[str]]:
        env_to_append: list[tuple[str, str]] = [
            ("PATH", f"{self.install_dir}/include"),
            ("LD_LIBRARY_PATH", f"{self.install_dir}/lib64"),
            ("LIB", f"{self.install_dir}/lib64")
        ]

        sh_cmds = self.append_envvar(env_to_append, shell='sh')
        csh_cmds = self.append_envvar(env_to_append, shell='csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}