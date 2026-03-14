#include <common.h>
#include <benchmark.h>

int main(void) {
  usize its_c = 10000000;
  usize its_m = 100000;
  usize its_e = 10000;
  usize its_r = 10000;
  usize reps  = 25;

  benchmark_all(its_c, its_m, its_e, its_r, reps);
}
