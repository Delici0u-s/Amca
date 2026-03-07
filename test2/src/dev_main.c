#include "common.h"
#include <stdio.h>

#include <de_vector.h>

/* comparator for integers (assumes elements are of type int) */
int cmp_int(const u0 *a, const u0 *b) {
  const int lhs = *(const int *)a;
  const int rhs = *(const int *)b;

  if (lhs < rhs) return -1;
  if (lhs > rhs) return 1;
  return 0;
}

bool pred_int(const u0 *item, u0 *data) { return cmp_int(item, data) == 0; }

void print_int(void *item, void *data) { printf("%i%s", *(int *)item, (char *)data); }
void add_int(void *item, void *data) { *(int *)item += *(int *)data; }

int moin(void) { //
  int    num   = 77;
  int    arr[] = {1, 2, 3};
  de_vec v1    = de_vec_create(sizeof(int));
  de_vec v2    = de_vec_create_from_array(sizeof(int), arr, 3);

  for (usize i = 0; i < 16; ++i) {
    de_vec_push_back(&v1, &i);
  }

  de_vec_concat(&v1, &v2);
  puts("Before transformations:");
  de_vec_foreach(&v1, print_int, "\n");
  puts("after transformations:");

  de_vec_erase_batch(&v1, 11, 4);

  de_vec_remove_all(&v1, &arr[2], cmp_int);

  *(int *)de_vec_find(&v1, pred_int, &arr[0]) -= 10;

  de_vec_foreach_range(&v1, add_int, &num, 5, 8);
  de_vec_foreach(&v1, print_int, "\n");

  puts("");
  printf("Vector capacity: %llu\n", de_vec_info_capacity(&v1));
  printf("Vector used: %llu\n", de_vec_info_size(&v1));
}
