#ifndef COMMON_H_
#define COMMON_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <immintrin.h>

/* macro impl stuff */
#define STRINGIFY(x) #x
#define STR(x) STRINGIFY(x)

/* just the usual suspects */
// clang-format off
typedef void          u0;
typedef size_t        usize;
typedef uintptr_t     uptr;
typedef ptrdiff_t     ptrdiff;

typedef uint8_t       u8;
typedef uint16_t      u16;
typedef uint32_t      u32;
typedef uint64_t      u64;

typedef int8_t        i8;
typedef int16_t       i16;
typedef int32_t       i32;
typedef int64_t       i64;

typedef float         f32;
typedef double        f64;
typedef long double   f87;

// clang-format on
#endif // COMMON_H_
