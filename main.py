import argparse
import os
import logging
import platform
import subprocess
from pathlib import Path
from typing import Literal

import extmgr

##############################################################################
############################### Set up logging ###############################
##############################################################################
logging.basicConfig(level=logging.INFO,
                    format='[External-Manager]  %(name)-20s     %(levelname)-7s     %(message)s',
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
    description="build external distributions",
)

parser.add_argument('-p', '--prefix',
                    help='installations prefix',
                    type=str,
                    dest='prefix',
                    action='store',
                    required=True)

parser.add_argument('-d', '--dist',
                    help='distribution to build',
                    type=str,
                    dest='dist',
                    action='store',
                    choices=list(extmgr.core.Executor().dists.keys()),
                    required=True)

parser.add_argument('-j', '--jobs',
                    help='number of processors to use',
                    type=pos_int,
                    default=1,
                    nargs='?',
                    const='',
                    dest='jobs',
                    action='store')

parser.add_argument('--build-dir',
                    help="build directory",
                    type=str,
                    default="build",
                    dest='build_dir',
                    action="store")

parser.add_argument('--patch-dir',
                    help="patches directory",
                    type=str,
                    dest='patch_dir',
                    action="store")

parser.add_argument('--dry-run',
                    help="only show the commands to be executed",
                    action="store_true",
                    default=False,
                    dest='dry_run')

build_type_group = parser.add_argument_group('build type')
build_type_mutex = build_type_group.add_mutually_exclusive_group()

build_type_mutex.add_argument('-opt', '--release',
                              help="build release version",
                              action='store_true',
                              default=False,
                              dest='build_type_opt')

build_type_mutex.add_argument('-dbg', '--debug',
                              help="build debug version",
                              action='store_true',
                              default=False,
                              dest='build_type_dbg')

build_type_mutex.add_argument('-rwd', '--relwithdebinfo',
                              help="build release with debug info",
                              action='store_true',
                              default=False,
                              dest='build_type_rwd')


args = parser.parse_args()

target_dist = args.dist
njobs = args.jobs
install_prefix = Path(args.prefix).resolve()
build_dir = Path(args.build_dir).resolve()
patch_dir = (Path(__file__).parent / 'patches').resolve() if args.patch_dir is None else Path(args.patch_dir).resolve()

cmake_build_type: Literal['Release', 'Debug', 'RelWithDebInfo'] = 'Release'
if args.build_type_opt:
    cmake_build_type = 'Release'
elif args.build_type_dbg:
    cmake_build_type = 'Debug'
elif args.build_type_rwd:
    cmake_build_type = 'RelWithDebInfo'


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

build_type_alias = {
    'Release': 'opt',
    'Debug': 'dbg',
    'RelWithDebInfo': 'rwd'
}[cmake_build_type]

build_flag = f'{platform.processor()}-{os_alias}-{gcc_version}-{build_type_alias}'

build_config = extmgr.BuildConfig(
    patch_dir=patch_dir,
    build_prefix=build_dir,
    install_prefix=install_prefix,
    cmake_build_type=cmake_build_type,
    build_flag=build_flag,
    n_jobs=njobs,
    dry_run=args.dry_run
)

logger.info(f"Distribution: {target_dist}")
logger.info(f"Install Prefix: {install_prefix}")
logger.info(f"Build Directory: {build_dir}")
logger.info(f"Number of jobs: {njobs}")
logger.info(f"Patches Directory: {patch_dir}")
logger.info(f"CMake Build Type: {cmake_build_type}")
logger.info(f"Build Flag: {build_flag}")

pkg_executor = extmgr.Executor()
pkg_executor.make_distribution(target_dist, build_config)
