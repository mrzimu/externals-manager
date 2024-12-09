from collections import defaultdict, deque
from .BasePackage import BasePackage


class BaseDistribution:
    def __init__(self, name: str) -> None:
        """
        Initialize a PackageDistribution object.

        Args:
            name (str): The name of the package distribution.

        Attributes:
            name (str): The name of the package distribution.
            _packages (dict): A dictionary to store packages.
            _dependencies (dict): A dictionary to store dependencies.
        """
        self.name = name

        self._packages: dict[str, BasePackage] = {}  # {package_name: package}
        self._dependencies: dict[str, list[str]] = {}  # {package_name: [dependency_name]}

    def add_package(self, package: BasePackage, dependencies: list[str] = None) -> None:
        """
        Adds a package to the distribution.

        Args:
            package (BasePackage): The package to be added.
            dependencies (list[str], optional): A list of package dependencies names. Defaults to None.

        Raises:
            ValueError: If the package already exists in the distribution.

        Returns:
            None
        """
        if package.name in self._packages:
            raise ValueError(f'Package {package.name} already exists in distribution {self.name}')

        self._packages[package.name] = package
        self._dependencies[package.name] = dependencies if dependencies is not None else []

    def sorted_packages(self) -> list[BasePackage]:
        """
        Returns a list of packages sorted by dependencies.

        Returns:
            list[BasePackage]: A list of packages sorted by dependencies.
        """

        in_degree = defaultdict(int)
        graph = defaultdict(list)

        # Initialize the graph
        for item, deps in self._dependencies.items():
            for dep in deps:
                graph[dep].append(item)
                in_degree[item] += 1
            if item not in in_degree:
                in_degree[item] = 0

        # Find all items with zero in-degree
        zero_in_degree_queue = deque([item for item in in_degree if in_degree[item] == 0])
        sorted_packages = []

        while zero_in_degree_queue:
            current_item = zero_in_degree_queue.popleft()
            sorted_packages.append(current_item)

            for neighbor in graph[current_item]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    zero_in_degree_queue.append(neighbor)

        # Check if there is a cycle
        if len(sorted_packages) != len(in_degree):
            raise ValueError("The graph has a cycle!")

        return [self._packages[pkg_name] for pkg_name in sorted_packages]
