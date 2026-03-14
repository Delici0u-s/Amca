### requirentments:
- git, python3

#### lugin reqs:
-  meson:
    - gcc, meson

---

## How to install
call `python3 install_uninstall_update.py` in the root directory

This adds `amca` and `amcapl`. use --help on each for information

install plugins with `amcapl i` which will be automatically be executed by amca based on files and dirs.

---

### Documentation will be updated sometime in the future when i fix lazyness in amca
For further Documentation install [Obsidian](https://obsidian.md/) and open `obsidian_vault` as vault in obsidian

---

### personal notes:
TODO:
- test windows capabilities
plugins
- create
    - Template
        - previous tempalte plugin


OLD AMCA TEMPLATE UPDATES REQUIRED:
| Refer to test/test2/meson.build for both fixes
- change the entire output_dir normalization to: `output_dir = meson.project_build_root() + '/' + output_dir`
- change globber to be in project directory and create a relative path in the command call `source_files = run_command(...)`if you have globber at the correct position you dont need to care



