import subprocess
from core import BasePackage, BuildConfig


class Gaudi(BasePackage):
    def __init__(self, build_config: BuildConfig, pre_env_cmds=None) -> None:
        super().__init__(build_config, pre_env_cmds)

        self.git_repo = 'https://gitlab.cern.ch/gaudi/Gaudi.git'

    @property
    def name(self) -> str:
        return 'Gaudi'

    @property
    def git_tag(self) -> str:
        return self.version

    def download(self) -> list[str]:
        cmds = []
        if self.source_dir.exists():
            cmds += [f'rm -rvf {self.source_dir}']

        cmds += [self.clone_git_repo(self.git_repo, self.git_tag)]
        return cmds

    def patch(self) -> list[str]:
        patch_file = f'{self.patch_dir}/{self.name}-{self.version}.patch'

        # Test if the patch file have been applied
        proc = subprocess.run(['patch', '-p1', '-N', '--dry-run', '-i', str(patch_file), '-d', str(self.source_dir)])
        if proc.returncode != 0:
            return []
        else:
            return [f'patch -p1 -N -i {patch_file} -d {self.source_dir}']

    def configure(self) -> list[str]:
        cmake_args = self.gen_cmake_args(
            {
                "CMAKE_BUILD_TYPE": self.build_config.cmake_build_type,
                "CMAKE_INSTALL_PREFIX": self.install_dir,
                "GAUDI_ENABLE_GAUDIALG": 'ON'
            }
        )
        return [f'cmake -B {self.build_dir} -S {self.source_dir} {cmake_args}']

    def build(self) -> list[str]:
        return [f'cmake --build {self.build_dir} --target install -- -j{self.build_config.n_proc}']

    def install(self) -> list[str]:
        return []

    def setup_cmds(self) -> dict[str, list[str]]:
        env_to_append: list[tuple[str, str]] = [
            ("PATH", f"{self.install_dir}/bin"),
            ("PATH", f"{self.install_dir}/include"),
            ("LD_LIBRARY_PATH", f"{self.install_dir}/lib"),
            ("CMAKE_PREFIX_PATH", f"{self.install_dir}/lib/cmake/Gaudi")
        ]

        sh_cmds = self.append_envvar(env_to_append, shell='sh')
        csh_cmds = self.append_envvar(env_to_append, shell='csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class Gaudi_v38r2(Gaudi):
    @property
    def version(self) -> str: return 'v38r2'
