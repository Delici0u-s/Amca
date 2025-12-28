../config
- general.json
- plugins
	- plugin_conf
	- installed_plugins
		- plugin
			- plugin.py
			- other source files...
		- ...

amcapl
- args:
	- enable
	- disable
	- install
	- uninstall
	- call

amca
- plugin
	- signature
		- should\_load(amca\_root\_dir\_info, working_ dir_info, dirparser)
		- load(args: list \[str])
	- plugin structure
		- amca_conf.json
			- takes_args: bool
		- init.py
		- ... up to user
- Arg giventh
	- amca
		- args
			- \<plugin>\_args.txt
				- each line is arg
- args
	- if no args
		- search backwards recursively \<max_depth> to find Amca folder, if found execute plugin should\_load and load
	- remove r
		- remove amca in current dir
	- new n
		- force amca in new path if doesnt exist alr
	- args a
		- edit args via cli interface