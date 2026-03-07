requirentments:
- git, python3  
plugin reqs:  
-  meson:  
    - gcc, meson  
This adds `amca` and `amcapl`. use --help for each for information  

install plugins with amcapl i which will be automatically be executed by amca based on files and dirs.  

## Documentation will be updated sometime in the future when i fix lazyness in amca
For further Documentation install [Obsidian](https://obsidian.md/) and open `obsidian_vault` as vault in obsidian

TODO:
- test windows capabilities

amcapl
- plugin updates
- more sources etc general polish
- command interface, not just cli

amca
- implement all --help and config options, increase option amount
- only call should_load on enabled plugins

plugins
- meson
    - meson better error message if meson is not available
    - more options for verbose, and implement quiet
    - proper logging
- autosh
    - create plugin that automatically executes amca_script.sh/bat in current dir


OLD AMCA TEMPLATE UPDATES REQUIRED:
| Refer to test/test2/meson.build for both fixes
- change the entire output_dir normalization to: `output_dir = meson.project_build_root() + '/' + output_dir`
- change globber to be in project directory and create a relative path in the command call `source_files = run_command(...)`if you have globber at the correct position you dont need to care


