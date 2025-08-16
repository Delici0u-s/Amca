// amca_impl/amca_runner_posix.c
#define _GNU_SOURCE
#include <libgen.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>


#ifdef __APPLE__
#include <mach-o/dyld.h>
#endif

int get_exe_path(char *buf, size_t bufsize) {
#ifdef __linux__
  ssize_t r = readlink("/proc/self/exe", buf, bufsize - 1);
  if (r <= 0)
    return -1;
  buf[r] = '\\0';
  return 0;
#elif defined(__APPLE__)
  uint32_t sz = (uint32_t)bufsize;
  if (_NSGetExecutablePath(buf, &sz) != 0)
    return -1;
  // _NSGetExecutablePath may return a non-resolved path; realpath below will
  // normalize
  return 0;
#else
  // fallback: use argv[0] will be handled by caller by passing it in; return -1
  // so caller falls back
  return -1;
#endif
}

int main(int argc, char *argv[]) {
  char exe_path[PATH_MAX] = {0};
  if (get_exe_path(exe_path, sizeof(exe_path)) != 0) {
    // fallback to argv[0] resolution
    if (realpath(argv[0], exe_path) == NULL) {
      fprintf(stderr, "Cannot determine executable path\n");
      return 1;
    }
  } else {
    // resolve symlinks
    char resolved[PATH_MAX];
    if (realpath(exe_path, resolved) != NULL) {
      strncpy(exe_path, resolved, sizeof(exe_path) - 1);
    }
  }

  // strip filename -> get directory
  char *dirc = strdup(exe_path);
  char *dname = dirname(dirc);

  // construct path to script: ../snakes/amca.py (mirror Windows version)
  char script[PATH_MAX];
  snprintf(script, sizeof(script), "%s/../snakes/amca.py", dname);

  // try absolute realpath of script
  char script_real[PATH_MAX];
  if (realpath(script, script_real) == NULL) {
    // try without resolving; maybe relative works
    strncpy(script_real, script, sizeof(script_real) - 1);
  }

  // Build argv for Python: use /usr/bin/env python3 for portability
  char **newargv = malloc(sizeof(char *) * (argc + 3));
  newargv[0] = "python3";
  newargv[1] = script_real;
  for (int i = 1; i < argc; ++i)
    newargv[i + 1] = argv[i];
  newargv[argc + 1] = NULL;

  // exec
  execvp("python3", newargv);

  perror("execvp");
  return 1;
}
