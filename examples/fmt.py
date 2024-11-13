from core import BuildConfig, BasePackage
from abc import abstractmethod


class Fmt(BasePackage):
    def __init__(self, build_config: BuildConfig, pre_env_cmds: list[str] = []) -> None:
        super().__init__(build_config, pre_env_cmds)

    @property
    def name(self) -> str: return 'fmt'

    @property
    def git_repo(self) -> str: return 'https://github.com/fmtlib/fmt.git'

    @property
    def git_tag(self) -> str: return self.version

    def download(self) -> list[str]:
        return [f'git clone --branch {self.git_tag} {self.git_repo} {self.source_dir}']

    def patch(self) -> list[str]:
        return []

    def configure(self) -> list[str]:
        cmake_args = self.gen_cmake_args({
            'CMAKE_BUILD_TYPE': self.build_config.cmake_build_type,
            'CMAKE_INSTALL_PREFIX': self.install_dir,
            'BUILD_SHARED_LIBS': 'TRUE'
        })
        return [f'cmake -B {self.build_dir} -S {self.source_dir} {cmake_args}']

    def build(self) -> list[str]:
        return [f'cmake --build {self.build_dir} --target install -- -j{self.build_config.n_proc}']

    def install(self) -> list[str]:
        return []

    def setup_cmds(self) -> dict[str, list[str]]:
        sh_cmds = [f"# {self.name}",
                   f"export PATH={self.install_dir}/include:$PATH",
                   f"export LD_LIBRARY_PATH={self.install_dir}/lib64:$LD_LIBRARY_PATH",
                   f"export LIB={self.install_dir}/lib64:$LIB",
                   f"export CMAKE_PREFIX_PATH={self.install_dir}/lib64/cmake/fmt:$CMAKE_PREFIX_PATH"]

        csh_cmds = [f"# {self.name}",
                    f'setenv PATH "{self.install_dir}/include:$PATH"',
                    f'setenv LD_LIBRARY_PATH "{self.install_dir}/lib:$LD_LIBRARY_PATH"',
                    f'setenv LIB "{self.install_dir}/lib:$LIB"',
                    f'setenv CMAKE_PREFIX_PATH "{self.install_dir}/lib/cmake/fmt:$CMAKE_PREFIX_PATH"']

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class Fmt_10_2_1(Fmt):
    @property
    def version(self) -> str: return '10.2.1'


class Fmt_11_0_2(Fmt):
    @property
    def version(self) -> str: return '11.0.2'

    @property
    def git_tag(self) -> str: return '11.0.2' # you can overwrite the git_tag property if needed
