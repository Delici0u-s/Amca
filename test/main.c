#include <stdio.h>

int p(char *str, char *arg);

int main(int argc, char *argv[static argc]) {
  printf("Hii: %i\nargs: ", argc);
  for (int i = 0; i < argc; ++i) {
    p("%s\t", argv[i]);
  }
  putchar('\n');
  return 0;
}
