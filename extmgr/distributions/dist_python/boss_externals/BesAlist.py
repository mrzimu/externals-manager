from extmgr import BasePackage, CmdList


class BesAlist(BasePackage):
    @property
    def git_tag(self) -> str:
        return '2024.12.08'

    @property
    def git_url(self) -> str:
        return "https://code.ihep.ac.cn/boss/boss_external/besalist.git"

    @property
    def name(self) -> str:
        return "BesAlist"

    @property
    def version(self) -> str:
        return "2024.12.08"

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
        lib_dir = self.install_dir / 'lib64' if (self.install_dir / 'lib64').exists() else self.install_dir / 'lib'

        env_to_append = [("INCLUDE", f"{self.install_dir}/include"),
                         ("LIB", f"{lib_dir}"),
                         ("LD_LIBRARY_PATH", f"{lib_dir}")]

        sh_cmds = self.append_envvar(env_to_append, 'sh')
        csh_cmds = self.append_envvar(env_to_append, 'csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}
