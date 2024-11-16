# env-setup

Environment setup is an important step when using packages that are not included in system environment paths. Usually there are 2 ways to setup an environment of package:

1. Exporting some environment variables (e.g. `PATH`, `LD_LIBRARY_PATH`, ...)

2. Sourcing some setup scripts

Such 2 ways can be finally expressed as some shell commands, and that's what `env-setup` does. `env-setup` controls generation of shell commands, these commands will be written to final setup scripts, or be executed during packages installation (For example, `pkg-b` depends on `pkg-a`, then before installing `pkg-b`, env-setup commands from `pkg-a` will be executed.)

> The order of 2 keys controls the commands' order in finally-generated setup scripts.

## export-env-vars

`export-env-vars` reads a dictionary. `key` is the name of environment variable, while `value` is a string (only 1 value) or a list of string (for multiple values).

An example of `export-env-vars` is:

```yaml
export-env-vars:
  PATH:
  - "@install_dir@/bin"
  - "@install_dir@/include"

  LD_LIBRARY_PATH: "@install_dir@/lib64"
  LIB: "@install_dir@/lib64"
  CMAKE_PREFIX_PATH: "@install_dir@/lib64/cmake/@name@"
```

This example will result in a shell commands generation (for `bash`):

```bash
# <package-name>
if [[ -n "$PATH" ]]; then
    export PATH="<install-dir>/bin:<install-dir>/include"
else
    export PATH="<install-dir>/bin:<install-dir>/include:$PATH"

if [[ -n "$LD_LIBRARY_PATH" ]]; then
    export LD_LIBRARY_PATH="<install-dir>/lib64"
else
    export LD_LIBRARY_PATH="<install-dir>/lib64:$LD_LIBRARY_PATH"
    
# LIB and CMAKE_PREFIX_PATH is omitted here
```

A corresponding `csh` version will be also generated. If you want to support other shells, extend [# TODO](what's the function should be extended?).



## exec-cmds

Differs to `export-env-vars`,  `exec-cmds` will directly execute commands specified by yaml configuration. To support different kinds of shell, `exec-cmds` reads a dictionary whose keys are the type of shell, and values are the commands to be executed.

An example of `exec-cmds` is:

```yaml
exec-cmds:
  sh:
    - echo Hello bash!
  csh:
    - echo Hello csh!
```

Commands will be exported into different setup scripts according to its keys.

