# Externals-Manager
A tool to help installing and managing external libraries with different versions and compiling configurations.

## Usage

By so far, availabe packages are quite limited. You can add more packages by inheriting `BasePackage` class. There are some references in `packages` directory.

### Add `package` and `release`

When we need a specific environment, usually we are requiring a specific combination of libraries and versions. Such combination is called a `release`, and its components are called `packages`. To prepare a `release`, we need to add some `package` first.

#### Prepare `package`

There are 2 packages in `packages/examples`. They are all inherited from `BasePackage` in `core/BasePackage.py`. You can add more packages by inheriting `BasePackage` class.

`BasePackage` has already defined some basic attributes and methods. You need to implement the following methods:

```python
@property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        ...

    @abstractmethod
    def download(self) -> list[str]:
        ...

    @abstractmethod
    def patch(self) -> list[str]:
        ...

    @abstractmethod
    def configure(self) -> list[str]:
        ...

    @abstractmethod
    def build(self) -> list[str]:
        ...

    @abstractmethod
    def install(self) -> list[str]:
        ...

    @abstractmethod
    def setup_cmds(self) -> dict[str, list[str]]:
        """
        Return `{shell: setup_cmd}` dictionary where `shell` is the shell type 
        and `setup_cmd` is the list of commands to be executed
        """
        ...
```

For `name` and `version`, you should return the name ("fmt" for example) and version ("10.2.1" for example). They will be used to create corresponding directories, so make sure they are valid for directory names.

For `download`, `patch`, `configure`, `build`, `install`, they should return a list of bash commands to download, patch, configure, build and install the package. Each method will be called only when the previous one is successfully executed, so you can add some `if` statements to return different commands based on the situation.

For `setup_cmds`, it should return a dictionary where the key is the shell type and the value is a list of commands to be executed. The shell type can be whatever you want, but it will be used to generate the setup script. For my own needs, I use `sh` and `csh` as the shell type. You can add more if you want.

There are some wrapper methods in `BasePackage` that you can use to make your code simpler. See `packages/examples` and `core/BasePackage.py` for more details.



#### Prepare `release`

After you have prepared all the packages you need, you can create a `release`. There are 2 ways to specify a `release`:

```python
releases = {
    'releaseA': {
        'fmt': Fmt_11_0_2,
        'catch2': Catch2_v3_7_1
    },

    'releaseB': {
        'tobuild': {
            'fmt': Fmt_10_2_1,
            'catch2': Catch2_v3_5_4},

        'depends': {
            'fmt': ['catch2'],  # if fmt depends on catch2, add it here
        }
    }
}
```

If there is no dependency between packages, you can use the first way. If there is, you can use the second way. In the second way, you must define both `tobuild` and `depends` keys. You can specify the dependencies in the `depends` field (therefore `tobuild` and `depends` cannot be used as package names).

Once the dependencies are specified, packages will be installed in the order of the dependency chain. Before one package is installed, it will also execute the `setup_cmds` of its dependencies.

Make sure that releases dictionary is imported in `releases.py` in the root directory, so that the main script can find it.

### Run Installation

After you have prepared the packages and releases, you can run the main script to install the packages.

```bash
python3 main.py -r releaseA -t Debug -p /path/to/MyExternals -j20
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
- setup
    - releaseA
        - x86_64-el9-gcc11-dbg.sh
        - x86_64-el9-gcc11-dbg.csh
```

Now by sourcing setup scripts in `setup/releaseA` you can use `fmt-11.0.2` and `Catch2-3.7.1` in your environment.

If you want to install another release or with another cmake-build-type, you can just run the command again with different arguments:

```bash
python3 main.py -r releaseB -t Debug -p /path/to/MyExternals -j20
python3 main.py -r releaseA -t Release -p /path/to/MyExternals -j20
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
    - releaseA
        - x86_64-el9-gcc11-dbg.sh
        - x86_64-el9-gcc11-opt.sh
        - x86_64-el9-gcc11-dbg.csh
        - x86_64-el9-gcc11-opt.csh
    - releaseB
        - x86_64-el9-gcc11-dbg.sh
        - x86_64-el9-gcc11-dbg.csh
```

Same versions of the package share the source directory, so they will not be downloaded and extracted again. If one package is already installed, it will not be reinstalled, only the setup script will be generated.

> Make your install prefix stable, so that the packages you have already installed will not be reinstalled.

### Force Reinstall

> **If you just want to update setup script, you don't need to remove anything. Just update the `setup_cmds` function and run the main script again.**

If you want to re-execute any step of the installation, you can remove corresponding items in `step_stamp.json`. For example, if you want to re-execute the `build` step of `fmt-11.0.2`, you can remove the `x86_64-OS-gcc11-build` in `fmt/11.0.2/step_stamp.json` file.

> Since source directory is shared with different `CMAKE_BUILD_TYPE` installation, key `download` and `patch` are unique in `step_stamp.json`.

You can also remove the whole directory of any version, so that the package in that version will be reinstalled from scratch.


### Activate Environment

After you have installed the packages, you can activate the environment by sourcing the setup script in `setup` directory.

