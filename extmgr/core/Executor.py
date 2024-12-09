from collections import defaultdict
import re
from typing import Any

from .ILog import ILog
from .BuildConfig import BuildConfig
from .BaseDistribution import BaseDistribution
from .BasePackage import BasePackage, CmdList


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args: Any, **kwds: Any) -> 'Executor':
        if cls not in cls._instances:
            instance = super(SingletonMeta, cls).__call__(*args, **kwds)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Executor(ILog, metaclass=SingletonMeta):
    def __init__(self) -> None:
        super().__init__()

        self.dists: dict[str, BaseDistribution] = {}

        # {package_name: {package_version: BasePackage}}
        self.packages: dict[str, dict[str, BasePackage]] = None
        self.update_packages()

    def add_package(self, package: BasePackage) -> None:
        """
        Add a package to the executor.

        Args:
            package (BasePackage): The package to be added.
        """
        if package.name not in self.packages:
            self.packages[package.name] = {}

        if self.packages[package.name].get(package.version):
            raise ValueError(f'Package {package.name} {package.version} already exists')

        self.packages[package.name][package.version] = package
        self.debug(f'Added package {package.name} {package.version}')

    def make_distribution(self, name: str, build_config: BuildConfig) -> bool:
        """
        Make the distribution.

        Args:
            dist (BaseDistribution): The distribution to be made.
            build_config (BuildConfig): The build configuration object.

        Returns:
            bool: True if the distribution was made successfully, False otherwise.
        """
        try:
            if name not in self.dists:
                self.error(f'Distribution {name} not found, did you forget to register it?')
                return False

            packages = self.dists[name].sorted_packages()
            env_setup_cmds: CmdList = []

            # Build each package
            for package in packages:
                self.info(f'Building package {package.name} {package.version}')

                package.set_config(build_config)
                if not package._make(env_setup_cmds):
                    self.error(f'Failed to make package {package.name}')
                    return False

                # Append setup commands
                new_env_setup_cmds = package.setup_cmds()['sh']
                if build_config.dry_run:
                    self.info('Add environment setup commands:')
                    self.info('')
                    self.info(' $ -----------------------')
                    for c in new_env_setup_cmds:
                        self.info(f' $ {c}')
                    self.info(' $ -----------------------')
                    self.info('')

                env_setup_cmds += new_env_setup_cmds

            # If dry run, print the full environment setup commands and return
            if build_config.dry_run:
                return True

            # Make setup commands
            setup_dir = build_config.install_prefix / 'setup-scripts' / name / build_config.build_flag
            setup_dir.mkdir(parents=True, exist_ok=True)

            setup_cmds: dict[str, CmdList] = defaultdict(list)

            for package in packages:
                for sh_type, cmds in package.setup_cmds().items():
                    setup_cmds[sh_type] += [f'# {package.name} - {package.version}'] + cmds + ['']

            for sh_type, cmds in setup_cmds.items():
                setup_file = setup_dir / f'{build_config.build_flag}.{sh_type}'
                try:
                    setup_file.write_text('\n'.join(cmds))
                except Exception as e:
                    self.error(f'Failed to write setup file {setup_file}: {e}')
                    return False

        except KeyboardInterrupt:
            self.error('Interrupted by user')
            return False

        return True

    def register_distribution(self, name: str, packages: list[tuple[str, str]], dependencies: dict[str, list[str]] = None) -> None:
        """
        Register a distribution.

        Args:
            name (str): The name of the distribution.
            packages (list[tuple[str, str]]): The packages to be registered.
            dependencies (dict[str, list[str]], optional): The dependencies of each package. Defaults to None.

        Raises:
            ValueError: If the distribution with the given name already exists.
            ValueError: If any of the packages in the list is not found.
            ValueError: If any of the dependencies is not found in the distribution.

        Returns:
            None
        """
        if dependencies is None:
            dependencies = {}

        if name in self.dists:
            raise ValueError(f'Distribution {name} already exists')

        # Check packages existence
        for pkg_name, pkg_version in packages:
            if pkg_name not in self.packages or pkg_version not in self.packages[pkg_name]:
                raise ValueError(f'Package {pkg_name} {pkg_version} not found')

        # Check dependencies existence
        pkg_names = [pkg_name for pkg_name, _ in packages]
        for pkg_name, pkg_deps in dependencies.items():
            for dep in pkg_deps:
                if dep not in pkg_names:
                    raise ValueError(
                        f'Dependency {dep} not found in distribution {name}. Dependency must be a member of the distribution')

        # Create the distribution
        dist = BaseDistribution(name)
        for pkg_name, pkg_version in packages:
            dist.add_package(self.packages[pkg_name][pkg_version], dependencies.get(pkg_name))

        self.dists[name] = dist
        self.debug(f'Registered distribution {name}')

    def update_packages(self) -> None:
        """
        Searches for packages and retrieves all subclasses of the BasePackage class.
        Only classes that have a name and version method are considered.

        Returns:
            dict: A dictionary containing all subclasses of BasePackage, grouped by package name and version.
        """

        def get_subclasses(cls, res: dict[str, dict[str, BasePackage]] = {}) -> dict[str, dict[str, BasePackage]]:
            """
            Recursively retrieves all subclasses of the given class.

            Args:
                cls (type): The class to retrieve subclasses from.

            Returns:
                dict: A dictionary containing all subclasses.
            """
            try:
                pkg = cls()
                pkg.name, pkg.version
                self.debug(f'Found package: {pkg.name} {pkg.version}')
                if pkg.name not in res:
                    res[pkg.name] = {}

                if pkg.version in res[pkg.name]:
                    raise ValueError(f'Package {pkg.name} {pkg.version} already exists')
                res[pkg.name][pkg.version] = pkg

            except (AttributeError, NotImplementedError, TypeError):
                pass

            subclasses = cls.__subclasses__()
            for subclass in subclasses:
                res |= get_subclasses(subclass)

            return res

        self.packages = get_subclasses(BasePackage)
