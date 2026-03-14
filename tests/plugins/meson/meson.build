project('CHANGEME', ['c'],
  version : '0.1',
  default_options : ['warning_level=3', 'c_std=c17', 'buildtype=release', 'optimization=3', 'debug=false'])

# These variables are required by amca. Do not change the names, but feel free to move them.
amca_var__meson__version_behaviour = '2.0.1' # DO NOT CHANGE
amca_var__meson__build_dir         = 'build'       # Relative to meson.build location
amca_var__meson__executable_name   = 'a'
amca_var__meson__install_dir       = '../compiled'  # Relative to build_dir
### end amca vars

# Collect source files — excludes the build directory, deduplicates across extensions
_glob_script = '''
import pathlib, sys
build = sys.argv[1]
seen = set()
for ext in ('*.c', '*.cpp', '*.cxx', '*.cc'):
    for p in pathlib.Path('.').rglob(ext):
        if p.parts and p.parts[0] == build:
            continue
        s = p.as_posix()
        if s not in seen:
            seen.add(s)
            print(s)
'''

_python = find_program('python3', 'python')

source_files = run_command(
  _python, '-c', _glob_script,
  amca_var__meson__build_dir,
  check : true
).stdout().strip().split('\n')

output_dir = meson.project_build_root() + '/' + amca_var__meson__install_dir

executable(amca_var__meson__executable_name,
  source_files,
  install     : true,
  install_dir : output_dir)
