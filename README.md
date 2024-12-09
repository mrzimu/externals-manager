# Externals-Manager
A tool to help installing and managing external libraries with different versions and compiling configurations.

## Usage

By so far, availabe packages are quite limited. You can add more packages by inheriting `BasePackage` class. There are some references in `extmgr/distributions/dist_python` directory.

### Add `package` and `distribution`

When we need a specific environment, usually we are requiring a specific combination of libraries and versions. Such combination is called a `distribution`, and its components are called `packages`. A packages directory should be:

```
- extmgr/distributions/dist_python
    - subdir1
        - __init__.py
        - PackageA.py
        - PackageB.py
        - ...

    - subdir2
        - __init__.py
        - PackageC.py
        - PackageD.py
        - ...

    - __init__.py # import all packages in sub-directories and specify the distribution
```

#### Prepare `package`

There are 2 packages in `extmgr/distributions/dist_python/examples`. They are all inherited from `BasePackage` in `extmgr/core/BasePackage.py`. You can add more packages by inheriting `BasePackage` class.

`BasePackage` has already defined some basic attributes and methods. You need to implement the following methods:

```python
@property
@abstractmethod
def name(self) -> str:
    """
    Return the package name

    Returns:
        str: Package name
    """
    raise NotImplementedError

@property
@abstractmethod
def version(self) -> str:
    """
    Return the package version

    Returns:
        str: Package version
    """
    raise NotImplementedError

@abstractmethod
def prepare_src_steps(self) -> list[tuple[StepName, CmdList]]:
    """
    Return a list of `(step_name, step_commands)` tuples. The `step_name` will be used as the
    key in the `build_stamp` file to store the step's timestamp. The `step_commands` should
    be a list of bash commands to be executed.

    You should use this method to prepare the source code for building. This could include
    downloading the source code, extracting it, patching it, etc.

    Returns:
        list[tuple[StepName, CmdList]]: List of `(step_name, [step_commands])` tuples
    """
    raise NotImplementedError

@abstractmethod
def build_steps(self) -> list[tuple[StepName, CmdList]]:
    """
    Return a list of `(step_name, step_commands)` tuples. The `step_name` will be used as the
    key in the `build_stamp` file to store the step's timestamp. The `step_commands` should
    be a list of bash commands to be executed.

    You should use this method to build and install the package. This could include running
    `configure`, `make`, `make install`, etc.

    Returns:
        list[tuple[StepName, CmdList]]: List of `(step_name, [step_commands])` tuples
    """
    raise NotImplementedError

@abstractmethod
def setup_cmds(self) -> dict[str, CmdList]:
    """
    Return `{shell_type: setup_cmd}` dictionary where `shell_type` is the type of shell
    (`sh`, `csh`, ...) and `setup_cmd` is the list of commands to be executed
    in that shell.

    You should use this method to set up the environment variables, paths, etc. needed to
    use the package.

    Returns:
        dict[str, CmdList]: `{shell_type: setup_cmd}` dictionary
    """
    raise NotImplementedError
```

For `name` and `version`, you should return string of name ("fmt" for example) and version ("10.2.1" for example). They will be used to create corresponding directories, so make sure they are valid for directory names.

`prepare_src_steps` and `build_steps` should return a list of tuples. Each tuple should contain a step name and a list of bash commands. The step name will be used as the key to store the timestamp of the step in the `step_stamp.json` file. The bash commands will be executed in order.

The difference between `prepare_src_steps` and `build_steps` is that steps in `prepare_src_steps` are common for all build types, they will only be executed for once. For example, downloading and extracting source code are common for all build types. But the steps in `build_steps` are specific for each build type. For example, building and installing the package are different for `Debug` and `Release` build types.

For `setup_cmds`, it should return a dictionary where the key is the shell type and the value is a list of commands to be executed. The shell type can be whatever you want, but it will be used to generate the setup script. For my own needs, I use `sh` and `csh` as the shell type. You can add more if you want.

There are some wrapper methods in `BasePackage` that you can use to make your code simpler. See `extmgr/distributions/dist_python/examples` and `extmgr/core/BasePackage.py` for more details.

#### Prepare `distribution`

Make sure your packages has been imported, then you can create a distribution by calling `Executor().register_distribution` in `extmgr/distributions/dist_python/__init__.py`.

```python
# first import your packages here

from extmgr.core import Executor

Executor().register_distribution(
    name="my_distribution",
    packages=[
        ('pkgA', 'versionA'),
        ('pkgB', 'versionB'),
        ...
    ],
    dependencies={
        'pkgA': ['pkgB', 'pkgC'],
        'pkgB': ['pkgD'],
        ...
    }
)
```

### Run Installation

After you have prepared all the packages and distributions, you can run the main script to install packages.

```bash
python3 main.py [-h] -p PREFIX -d {distA, distB, distC} [-j [JOBS]] [--build-dir BUILD_DIR] [--patch-dir PATCH_DIR] [--dry-run] [-opt | -dbg | -rwd]
```

When command finishes, you will find a directory structure like this in `/path/to/MyExternals`:

```
- Catch2
    - v3.7.1
        - src
        - x86_64-el9-gcc11-dbg
        - step_stamp.json
- fmt
    - 11.0.2
        - src
        - x86_64-el9-gcc11-dbg
        - step_stamp.json
- setup-scripts
    - distA
        - x86_64-el9-gcc11-dbg.sh
        - x86_64-el9-gcc11-dbg.csh
```

Now by sourcing setup scripts in `setup-scripts/distA` you can use `fmt-11.0.2` and `Catch2-3.7.1` in your environment.

If you want to install another release or with another cmake-build-type, you can just run the command again with different arguments:

```bash
python3 main.py -d distA -p /path/to/MyExternals -j20
python3 main.py -d distB -p /path/to/MyExternals -j -dbg
```

The direcotry structure will be updated to:

```
- Catch2
    - v3.5.4
        - src
        - x86_64-el9-gcc11-dbg
        - step_stamp.json
    - v3.7.1
        - src
        - x86_64-el9-gcc11-dbg
        - x86_64-el9-gcc11-opt
        - step_stamp.json
- fmt
    - 10.2.1
        - src
        - x86_64-el9-gcc11-dbg
        - step_stamp.json
    - 11.0.2
        - src
        - x86_64-el9-gcc11-dbg
        - x86_64-el9-gcc11-opt
        - step_stamp.json
- setup
    - distA
        - x86_64-el9-gcc11-dbg.sh
        - x86_64-el9-gcc11-opt.sh
        - x86_64-el9-gcc11-dbg.csh
        - x86_64-el9-gcc11-opt.csh
    - distB
        - x86_64-el9-gcc11-dbg.sh
        - x86_64-el9-gcc11-dbg.csh
```

Same versions of one package share its source directory, so they will not be downloaded and extracted again. If one package is already installed, it will not be reinstalled, only the setup script will be generated.

> Make your install prefix reusable, so that the packages you have already installed will not be reinstalled.

### Force Reinstall

> **If you just want to update setup script, you don't need to do anything. Just update the `setup_cmds` function and run main script again.**

If you want to re-execute any step of the installation, you can remove corresponding items in `step_stamp.json`. For example, if you want to re-execute `build` step of `fmt-11.0.2`, you can remove the `x86_64-OS-gcc11-build` in `fmt/11.0.2/step_stamp.json` file.

> Since source directory is shared with different `CMAKE_BUILD_TYPE` installation, some keys are unique in `step_stamp.json`.

You can also remove the whole package directory of any version, so that the package in that version will be reinstalled from scratch.


### Activate Environment

After you have installed the packages, you can activate the environment by sourcing the setup script in `setup-script` directory.

