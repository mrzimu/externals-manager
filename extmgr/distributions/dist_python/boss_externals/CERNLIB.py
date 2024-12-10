from abc import abstractmethod
from extmgr import BasePackage, CmdList


class CERNLIB(BasePackage):
    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def git_tag(self) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return 'CERNLIB'

    @property
    def git_url(self) -> str:
        return 'https://gitlab.cern.ch/averbyts/cernlib-free-test.git'

    def prepare_src_steps(self) -> list[tuple[str, CmdList]]:
        clone_cmds = self.clone_git_repo(self.git_url, self.git_tag)

        patch_file = self.patch_dir / f'{self.name}-{self.version}.patch'
        patch_cmds = self.apply_patch(patch_file)

        return [
            ('clone', clone_cmds),
            ('patch', patch_cmds)
        ]

    def build_steps(self) -> list[tuple[str, CmdList]]:
        config_cmds = self.cmake_config(
            {
                'CERNLIB_POSITION_INDEPENDENT_CODE': 'ON',
                'DCERNLIB_BUILD_SHARED': 'ON'
            }
        )

        build_cmds = self.cmake_build()

        return [
            ('config', config_cmds),
            ('build', build_cmds)
        ]

    def setup_cmds(self) -> dict[str, list[str]]:
        lib_dir = self.install_dir / 'lib64' if (self.install_dir / 'lib64').exists() else self.install_dir / 'lib'
        env_to_append = [("INCLUDE", f"{self.install_dir}/include"),
                         ("LIB", f"{lib_dir}"),
                         ("PATH", f"{self.install_dir}/bin"),
                         ("LD_LIBRARY_PATH", f"{lib_dir}")]

        sh_cmds = self.append_envvar(env_to_append, shell='sh')
        csh_cmds = self.append_envvar(env_to_append, shell='csh')

        return {'sh': sh_cmds,
                'csh': csh_cmds}


class CERNLIB_2006120(CERNLIB):
    @property
    def version(self) -> str: return '2024.06.12.0'

    @property
    def git_tag(self) -> str: return 'cernlib-2024.06.12.0'
