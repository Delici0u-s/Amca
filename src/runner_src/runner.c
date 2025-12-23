/* command here as test, will be replaced by the python setup thingy */
#define COMMAND "echo"

#include <stdio.h>

#ifdef _WIN32
#include <process.h> // _execvp
#define execvp _execvp
#else
#include <unistd.h> // execvp
#endif

int main(int argc, char *argv[]) {
  // Build argument vector:
  // ["echo", argv[1], argv[2], ..., NULL]

  char *exec_argv[argc + 1];

  exec_argv[0] = COMMAND;

  for (int i = 1; i < argc; ++i) {
    exec_argv[i] = argv[i];
  }

  exec_argv[argc] = NULL;

  execvp(COMMAND, exec_argv);

  // Only reached on error
  perror("execvp failed");
  return 1;
}
