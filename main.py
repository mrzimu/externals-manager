import argparse
import os
import logging
import subprocess
import platform
from pathlib import Path
from typing import Literal
from collections import defaultdict, deque

from core import BuildConfig, BasePackage
from releases import releases

##############################################################################
############################### Set up logging ###############################
##############################################################################
logging.basicConfig(level=logging.INFO,
                    format='[External-Manager] %(name)-20s     %(levelname)-7s     %(message)s',
                    datefmt='%m-%d %H:%M')

logger = logging.getLogger('Main')


##############################################################################
############################## Parse Arguments ###############################
##############################################################################


def pos_int(value) -> str:
    if value is None or value == '':
        return ''

    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")

    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")

    return str(ivalue)


parser = argparse.ArgumentParser(
    prog="python3 main.py",
    description="Build BOSS external packages",
)

parser.add_argument('-r', '--release',
                    help="Release version of combinition of external packages",
                    type=str,
                    choices=releases,
                    dest='release',
                    action='store',
                    required=True)

parser.add_argument('-t', "--build-type",
                    help="CMAKE_BUILD_TYPE, Release or Debug",
                    type=str,
                    choices=["Release", "Debug"],
                    default="Release",
                    dest="build_type",
                    action="store")

parser.add_argument('-j', "--jobs",
                    help="Number of processors to use",
                    type=pos_int,
                    default=os.cpu_count(),
                    nargs='?',
                    const='',
                    dest='jobs',
                    action="store")

parser.add_argument('-p', "--prefix",
                    help="Install prefix",
                    type=str,
                    dest='prefix',
                    action="store",
                    required=True)

parser.add_argument('--build-dir',
                    help="Build directory",
                    type=str,
                    default="build",
                    dest='build_dir',
                    action="store")

parser.add_argument('--dry-run',
                    help="Only show the commands to be executed",
                    action="store_true",
                    default=False,
                    dest='dry_run')

args = parser.parse_args()

njobs = args.jobs
install_prefix = Path(args.prefix).resolve()
build_dir = Path(args.build_dir).resolve()
patch_dir = (Path(__file__).parent / 'patches').resolve()

if njobs != '' and int(njobs) > os.cpu_count():
    logger.warning(
        f"Number of processors to use is larger than the number of available processors, using {os.cpu_count()} instead")
    njobs = os.cpu_count()

logger.info(f"Release: {args.release}")
logger.info(f"Build Type: {args.build_type}")
logger.info(f"Number of jobs: {njobs}")
logger.info(f"Install Prefix: {install_prefix}")
logger.info(f"Build Directory: {build_dir}")
logger.info(f"Patch Directory: {patch_dir}")

if not args.dry_run:
    build_dir.mkdir(parents=True, exist_ok=True)

##############################################################################
############################ Determine build flag ############################
##############################################################################
try:
    # Read OS release info
    org_rel_info = subprocess.check_output("cat /etc/os-release", shell=True).decode('utf-8').strip().splitlines()
    os_release = {line.split('=')[0]: line.split('=')[1].strip('"') for line in org_rel_info if line != ''}

    os_name = os_release['ID']
    os_version = os_release['VERSION_ID'].split('.')[0]

    if os_name == 'almalinux':
        os_name = 'el'

    os_alias = os_name + os_version
    gcc_version = 'gcc' + subprocess.check_output(['gcc', '-dumpversion']).decode().strip().split('.')[0]

except Exception as e:
    logger.error(f"Failed to get OS release info: {e}")
    exit(1)

if args.build_type == 'Release':
    build_type_alias = 'opt'
elif args.build_type == 'Debug':
    build_type_alias = 'dbg'
else:
    build_type_alias = args.build_type.lower()

config_alias = f'{platform.processor()}-{os_alias}-{gcc_version}-{build_type_alias}'

build_config = BuildConfig(
    patch_dir=patch_dir,
    build_dir=build_dir,
    install_dir=install_prefix,
    cmake_build_type=args.build_type,
    config_alias=config_alias,
    n_proc=njobs,
    dry_run=args.dry_run
)

logger.info(f"Build config: {build_config}")

##############################################################################
########################### Configure build rules ############################
##############################################################################
tobuild_dict = {}
depend_rule_dict = {}

if 'tobuild' in releases[args.release] and 'depends' in releases[args.release]:
    tobuild_dict: dict[str, BasePackage] = releases[args.release]['tobuild']
    depend_rule_dict: dict[str, list[str]] = releases[args.release]['depends']
elif 'tobuild' not in releases[args.release] and 'depends' not in releases[args.release]:
    tobuild_dict: dict[str, BasePackage] = releases[args.release].copy()
    depend_rule_dict: dict[str, list[str]] = {k: [] for k in tobuild_dict.keys()}
else:
    logger.error("You must specify both 'tobuild' and 'depends' in the release configuration!")
    exit(1)

# Add empty dependencies for packages not in the dependency list
for k in tobuild_dict:
    if k not in depend_rule_dict:
        depend_rule_dict[k] = []

build_status: dict[str, bool] = {k: False for k in tobuild_dict.keys()}


##############################################################################
####################### Begin to build, do not edit! #########################
##############################################################################


# Determine the build order
def topological_sort(dependency_dict: dict[str, list[str]]):
    """
    Topological sort of a graph represented by a dictionary of dependencies,
    just to sort the build order of the packages.
    """
    in_degree = defaultdict(int)
    graph = defaultdict(list)

    # Initialize the graph
    for item, deps in dependency_dict.items():
        for dep in deps:
            graph[dep].append(item)
            in_degree[item] += 1
        if item not in in_degree:
            in_degree[item] = 0

    # Find all items with zero in-degree
    zero_in_degree_queue = deque([item for item in in_degree if in_degree[item] == 0])
    sorted_order = []

    while zero_in_degree_queue:
        current_item = zero_in_degree_queue.popleft()
        sorted_order.append(current_item)

        for neighbor in graph[current_item]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                zero_in_degree_queue.append(neighbor)

    # Check if there is a cycle
    if len(sorted_order) != len(in_degree):
        raise ValueError("The graph has a cycle!")

    return sorted_order


build_order = topological_sort(depend_rule_dict)

logger.info(f"Build order: {build_order}")

# Instantiate the package objects
for pkg_name in build_order:

    # Get the setup commands of the dependencies
    pre_env_cmds = []
    for dep in depend_rule_dict[pkg_name]:
        pre_env_cmds += tobuild_dict[dep].setup_cmds()['sh']

    # Instantiate the package object
    tobuild_dict[pkg_name] = tobuild_dict[pkg_name](build_config, pre_env_cmds)

# Check if there are packages with the same name
if len(set([pkg.name for pkg in tobuild_dict.values()])) != len(tobuild_dict):
    logger.error("There are packages with the same name!")
    exit(1)

# Build the packages
for pkg_name in build_order:
    pkg = tobuild_dict[pkg_name]
    logger.info(f"Building {pkg.name}-{pkg.version}")

    # Check dependencies
    for dep in depend_rule_dict[pkg_name]:
        if not build_status[dep]:
            logger.error(f"Dependency {dep} of {pkg.name} is not built yet!")
            exit(1)

    # Build the package
    if not pkg._make():
        logger.error(f"Failed to build {pkg.name}-{pkg.version}")
        exit(1)

    build_status[pkg_name] = True
    logger.info(f"{pkg.name}-{pkg.version} is built successfully")

# Generate setup scripts
setup_prefix: Path = install_prefix / 'setup' / args.release / config_alias
setup_prefix.parent.mkdir(parents=True, exist_ok=True)

setup_cmds: dict[str, list[str]] = defaultdict(list)
for pkg in tobuild_dict.values():
    for shell, cmds in pkg.setup_cmds().items():
        setup_cmds[shell] += ([f'# {pkg.name}'] + cmds + [''])

for suffix, cmds in setup_cmds.items():
    setup_file = setup_prefix.with_suffix('.' + suffix)
    with open(setup_file, 'w') as f:
        f.write('\n'.join(cmds))
    logger.info(f"Setup script {setup_file} is generated.")

logger.info("All packages are built successfully!")
