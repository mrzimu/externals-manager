from core import BuildConfig, BasePackage


class Fmt(BasePackage):
    def __init__(self, build_config: BuildConfig, pre_env_cmds=None) -> None:
        super().__init__(build_config, pre_env_cmds)

        self.git_repo = 'https://github.com/fmtlib/fmt.git'

    @property
    def name(self) -> str: return 'fmt'

    @property
    def git_tag(self) -> str: return self.version

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
            'BUILD_SHARED_LIBS': 'TRUE'
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
            ("LIB", f"{self.install_dir}/lib64"),
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
