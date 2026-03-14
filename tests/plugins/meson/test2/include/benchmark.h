#define _POSIX_C_SOURCE 199309L // ← must be first, before everything

#include <common.h>
#include <de_vector.h>
#include <stdarg.h>
#include <stdio.h>
#include <time.h>

static inline double timespec_diff_sec(struct timespec start, struct timespec end) { return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9; }
/*
#define bench_for_start(iterations, repeats, ops_per_sec_output, for_body)     \
  do {                                                                         \
    for (usize round_counter = 0; round_counter < repeats; ++round_counter) {  \
      struct timespec start, end;                                              \
      clock_gettime(CLOCK_MONOTONIC, &start);                                  \
      for (usize i = 0; i < iterations; i++) {                                 \
        for_body                                                               \
      }                                                                        \
      clock_gettime(CLOCK_MONOTONIC, &end);                                    \
      ops_per_sec_output +=                                                    \
          (usize)((double)iterations / timespec_diff_sec(start, end));         \
    }                                                                          \
    ops_per_sec_output /= (double)repeats;                                     \
  } while (0)
*/
#define CONCAT2(a, b) a##b
#define CONCAT(a, b)  CONCAT2(a, b)
#define bench_for_start(iterations, repeats, ops_out, repeat_body, for_body)                                                                                                       \
  do {                                                                                                                                                                             \
    double CONCAT(__bench_acc_, __LINE__) = 0.0;                                                                                                                                   \
    for (usize CONCAT(__bench_round_, __LINE__) = 0; CONCAT(__bench_round_, __LINE__) < (repeats); ++CONCAT(__bench_round_, __LINE__)) {                                           \
      {                                                                                                                                                                            \
        repeat_body                                                                                                                                                                \
      }                                                                                                                                                                            \
      struct timespec CONCAT(__bench_start_, __LINE__), CONCAT(__bench_end_, __LINE__);                                                                                            \
      clock_gettime(CLOCK_MONOTONIC, &CONCAT(__bench_start_, __LINE__));                                                                                                           \
      for (usize i = 0; i < (iterations); ++i) {                                                                                                                                   \
        for_body                                                                                                                                                                   \
      }                                                                                                                                                                            \
      clock_gettime(CLOCK_MONOTONIC, &CONCAT(__bench_end_, __LINE__));                                                                                                             \
      double CONCAT(__bench_elapsed_, __LINE__) = timespec_diff_sec(CONCAT(__bench_start_, __LINE__), CONCAT(__bench_end_, __LINE__));                                             \
      if (CONCAT(__bench_elapsed_, __LINE__) > 0.0) {                                                                                                                              \
        CONCAT(__bench_acc_, __LINE__) += (double)(iterations) / CONCAT(__bench_elapsed_, __LINE__);                                                                               \
      }                                                                                                                                                                            \
    }                                                                                                                                                                              \
    /* final average (rounded toward zero) */                                                                                                                                      \
    (ops_out) = (usize)(CONCAT(__bench_acc_, __LINE__) / (double)(repeats));                                                                                                       \
  } while (0)

de_vec bench_vec_t_fill(usize amount) {
  de_vec out = de_vec_create(sizeof(int));
  for (usize i = 0; i <= amount; ++i) {
    de_vec_push_back(&out, &i);
  }
  return out;
}
/*
usize bench_vec_NAME(const usize iterations, const usize repeats) {
  usize ops_per_second = 0;
  de_vec v = bench_vec_t_fill(500);

  bench_for_start(iterations, repeats, ops_per_second, {});

  return ops_per_second;
}
*/

usize bench_vec_get(const usize iterations, const usize repeats) {
  usize        ops_per_second = 0;
  de_vec       v              = bench_vec_t_fill(501);
  volatile int buf;

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = bench_vec_t_fill(501);
    },
    { buf = *(int *)de_vec_get(&v, i % 500); }
  );

  printf("%i", buf);
  return ops_per_second;
}

usize bench_vec_set(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = bench_vec_t_fill(501);

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = bench_vec_t_fill(501);
    },
    { de_vec_set(&v, i % 500, &i); }
  );

  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}
usize bench_vec_swap(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = bench_vec_t_fill(500);

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = bench_vec_t_fill(500);
    },
    { de_vec_swap_elements(&v, i % 500, i % 35); }
  );

  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}
usize bench_vec_reserve(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = de_vec_create(sizeof(int));

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = de_vec_create(sizeof(int));
    },
    { de_vec_reserve(&v, i); }
  );

  de_vec_push_back(&v, &ops_per_second);
  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}
usize bench_vec_resize(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = de_vec_create(sizeof(int));

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = de_vec_create(sizeof(int));
    },
    { de_vec_resize(&v, i * sizeof(int)); }
  );

  de_vec_push_back(&v, &ops_per_second);
  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}
usize bench_vec_emplace_back(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = de_vec_create_with_capacity(sizeof(int), 10000);

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = de_vec_create_with_capacity(sizeof(int), 10000);
    },
    { de_vec_push_back(&v, &i); }
  );

  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}
usize bench_vec_insert(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = bench_vec_t_fill(500);

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = bench_vec_t_fill(500);
    },
    { de_vec_insert(&v, i % 500, &i); }
  );

  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}

usize bench_vec_pop_back(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = bench_vec_t_fill(iterations + 5);

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = bench_vec_t_fill(iterations + 5);
    },
    { de_vec_pop_back(&v); }
  );

  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}

usize bench_vec_pop_back_destructor(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = bench_vec_t_fill(iterations + 5);

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = bench_vec_t_fill(iterations + 5);
    },
    { de_vec_pop_back_with_destructor(&v); }
  );

  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}

usize bench_vec_pop_back_keep(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = bench_vec_t_fill(iterations + 5);
  int    buf;

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = bench_vec_t_fill(iterations + 5);
    },
    { de_vec_pop_back_keep(&v, &buf); }
  );

  printf("%i", buf);
  return ops_per_second;
}

usize bench_vec_erase(const usize iterations, const usize repeats) {
  usize  ops_per_second = 0;
  de_vec v              = bench_vec_t_fill(iterations + 500);

  bench_for_start(
    iterations,
    repeats,
    ops_per_second,
    {
      de_vec_delete(&v);
      v = bench_vec_t_fill(iterations + 500);
    },
    { de_vec_erase(&v, i % 500); }
  );

  printf("%i", *(int *)de_vec_get(&v, 0));
  return ops_per_second;
}

typedef struct {
  const float ops;
  const char *name;
} result;

void print_table(usize *count, ...) {
  va_list args;
  va_start(args, *count);

  puts("");
  puts("");
  printf("+---------------------+-----------+\n");
  printf("| %-19s | %-9s |\n", "Name", "MOps/sec");
  printf("+---------------------+-----------+\n");

  for (int i = 0; i < *count; i++) {
    result r = va_arg(args, result);
    printf("| %-19s | %9.4f |\n", r.name, r.ops);
  }

  printf("+---------------------+-----------+\n");

  va_end(args);
}

#define r(_name, _ops) ((result){.ops = (++arg_count, (_ops / (double)1000000)), .name = #_name})

void benchmark_all(usize iterations_cheap, usize iterations_mid, usize iterations_expensive, usize iterations_rolex, usize repeats) {
  usize arg_count = 0;
  print_table(
    &arg_count,
    r(get, bench_vec_get(iterations_cheap, repeats)),
    r(get, bench_vec_get(iterations_cheap, repeats)),
    r(set, bench_vec_set(iterations_mid, repeats)),
    r(swap, bench_vec_swap(iterations_mid, repeats)),
    r(reserve, bench_vec_reserve(iterations_rolex, repeats)),
    r(resize, bench_vec_resize(iterations_expensive, repeats)),
    r(emplace_back, bench_vec_emplace_back(iterations_cheap, repeats)),
    r(insert, bench_vec_insert(iterations_rolex, repeats)),
    r(pop_back, bench_vec_pop_back(iterations_cheap, repeats)),
    r(pop_back_destructor, bench_vec_pop_back_destructor(iterations_cheap, repeats)),
    r(pop_back_keep, bench_vec_pop_back_keep(iterations_cheap, repeats)),
    r(erase, bench_vec_erase(iterations_rolex, repeats))
  );
}
