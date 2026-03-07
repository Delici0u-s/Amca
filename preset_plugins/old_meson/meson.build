project('CHANGEME', ['c'],
  version : '0.1',
  default_options : ['warning_level=3', 'c_std=c17', 'buildtype=release', 'optimization=3', 'debug=false'])

################ EXAMPLE FILE #######################

# These variables are required by amca. Do not change the names, but feel free to move them
amca_var__meson__version_behaviour = '2.0.1' # DO NOT CHANGE
amca_var__meson__build_dir = 'build' # Relative to meson.build location

amca_var__meson__executable_name = 'a'
amca_var__meson__install_dir = '/../compiled' # Relative to build_dirVj### end amca vars

source_files = ['main.c']
output_dir = meson.project_build_root() + amca_var__meson__install_dir

executable(amca_var__meson__executable_name,
  source_files,
  install : true,
  install_dir : output_dir)

