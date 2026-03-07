#ifndef DE_CONTAINER_VECTOR_HEADER
#define DE_CONTAINER_VECTOR_HEADER
#ifdef __cplusplus
extern "C" {
#endif

/*
TODO:
  implement initialized check
*/

/*
to get function definitions #define DE_CONTAINER_VECTOR_IMPLEMENTATION before
any #include

IMPORTANT: If you keep a data* to a value stored in the vector, this pointer
           will go invalid if the vector size will be changed, so ensure you use
           get again once a resize might happen
*/

// #define DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
/* clang-format off */
/* possible options to set before 'first' include and IMPLEMENTATION */
#ifndef DE_CONTAINER_VECTOR_OPTIONS
#ifdef DE_CONTAINER_VECTOR_OPTIONS
/* if defined removes assert checks for _idx */
#define DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
#define DE_OPTIONS_VECTOR_DEFAULT_DESTRUCTOR defaults to nothing happening, as zeroing data would be slower lol (void foo(u0* const data){})

#define DE_OPTIONS_VECTOR_INITIAL_SIZE defaults to 8 /* i suggest a value resulting from 2^n */
#define DE_OPTIONS_VECTOR_GROWTH_FACTOR defaults to 2 /* i suggest a value resulting from 2^n */
#define DE_OPTIONS_VECTOR_DATA_PTR_MALLOC_FUNCTION defaults to malloc from stdlib
#define DE_OPTIONS_VECTOR_DATA_PTR_FREE_FUNCTION defaults to free
#endif
#endif

#ifdef DE_CONTAINER_VECTOR_IMPLEMENTATION
#define DE_CONTAINER_VECTOR_API
#else
#define DE_CONTAINER_VECTOR_API extern
#endif
#define DE_CONTAINER_VECTOR_INTERNAL

/* declarations */
#include <common.h>
#include <stdbool.h>

/* defaults to free */
typedef u0 (*de_vec_destructor_func)(u0 *_p);

/* comparator: returns <0, 0, >0 like qsort */
typedef int (*de_vec_cmp_func)(const u0 *a, const u0 *b);
/* example: 
int cmp_int(const void *a, const void *b) {
  const int lhs = *(const int *)a;
  const int rhs = *(const int *)b;

  if (lhs < rhs) return -1;
  if (lhs > rhs) return 1;
  return 0;
}
*/

/* predicate: returns true for match */
typedef bool (*de_vec_pred_func)(const u0 *item, u0 *data);
/* example: 
  bool pred_int(const void *item, void *data) 
  { return cmp_int(item, data) == 0; }
*/

/* foreach callback: item is mutable, ctx user-provided */
typedef u0 (*de_vec_foreach_func)(u0 *item, u0 *data);
/* example: 
  void prnt_int(void* item, void* data){
    printf("%i%s", *(int*)item, (char*)data);
  }
*/

/* more like byte lol */
#define DE_C_VEC_VOID_REPLACEMENT u8
typedef struct {
  usize item_size;

  usize capacity;
  usize used;

  DE_C_VEC_VOID_REPLACEMENT* data;

  de_vec_destructor_func destructor;
} de_vec;

/* 
  constructors
*/
/* returns a vector. _item_size in bytes*/
DE_CONTAINER_VECTOR_API de_vec
de_vec_create(
  const usize        _item_size
);

DE_CONTAINER_VECTOR_API de_vec
de_vec_create_with_capacity(
  const usize        _item_size,
  usize        _initial_capacity
);

DE_CONTAINER_VECTOR_API de_vec
de_vec_create_verbose(
  const usize                  _item_size,
  const de_vec_destructor_func _destructor_function
);

DE_CONTAINER_VECTOR_API de_vec
de_vec_create_with_capacity_verbose(
  const usize                  _item_size,
  usize                  _initial_capacity,
  const de_vec_destructor_func _destructor_function
);

/* initialize from existing contiguous array (copies data) */
DE_CONTAINER_VECTOR_API de_vec
de_vec_create_from_array(
  const usize  _item_size,
  const u0    *_data,
  const usize  _count
);
/* copies raw data from vector */
DE_CONTAINER_VECTOR_API de_vec
de_vec_create_from_vector(
  const de_vec* const _src
);

/* set used amount to 0 */
DE_CONTAINER_VECTOR_API u0
de_vec_clear(
  de_vec *const           _vec
);

/* call element destructor on each item, but keep capacity*/
DE_CONTAINER_VECTOR_API u0
de_vec_clear_with_destructor(
  de_vec *const           _vec
);

/* delete entire vector */
DE_CONTAINER_VECTOR_API u0
de_vec_delete(
  de_vec *const           _vec
);

/* delete entire vector, call destructor on each item */
DE_CONTAINER_VECTOR_API u0
de_vec_delete_with_destructor(
  de_vec *const           _vec
);

/* set or replace element destructor function */
DE_CONTAINER_VECTOR_API u0
de_vec_set_destructor(
  de_vec *const              _vec,
  de_vec_destructor_func     _destructor
);

/*
  Info getters
*/

DE_CONTAINER_VECTOR_API usize
de_vec_info_item_size(
  de_vec *const _vec
);

/* current number of stored elements */
DE_CONTAINER_VECTOR_API usize
de_vec_info_size(
  de_vec *const _vec
);

/* underlying allocated capacity in elements */
DE_CONTAINER_VECTOR_API usize
de_vec_info_capacity(
  de_vec *const _vec
);

/* raw data pointer (start) */
DE_CONTAINER_VECTOR_API u0*
de_vec_info_raw_data(
  de_vec *const _vec
);

/* raw data pointer (one-past-end of used elements) */
DE_CONTAINER_VECTOR_API u0*
de_vec_info_raw_data_end(
  de_vec *const _vec
);

DE_CONTAINER_VECTOR_API bool
de_vec_info_empty(
  de_vec *const _vec
);

/*
  Capacity / resizing
*/

/* reserves up to size, will not shrink/loose data */
DE_CONTAINER_VECTOR_API u0
de_vec_reserve(
  de_vec *const _vec,
  usize   _size
);

/* shrinks vector, will not delete data*/
DE_CONTAINER_VECTOR_API u0
de_vec_shrink_to_fit(
  de_vec *const _vec
);

/* resizes vector, will delete data if necessary */
DE_CONTAINER_VECTOR_API u0
de_vec_resize(
  de_vec *const       _vec,
  const usize         _new_size
);

/*
  Element access
*/

/* return address of the element at position _idx*/
DE_CONTAINER_VECTOR_API u0*
de_vec_get(
  de_vec *const    _vec,
  const usize      _idx
);

/* de_vec_get but with an automatic type* cast */
#define de_vec_getA(type, _vec, _idx) ((type*)de_vec_get(_vec, _idx))

/* copies _new_element into the position _idx*/
DE_CONTAINER_VECTOR_API u0
de_vec_set(
  de_vec *const         _vec,
  const usize           _idx,
  const u0 *const       _new_element
);


/* swaps two elements */
DE_CONTAINER_VECTOR_API u0
de_vec_swap_elements(
  de_vec *const      _vec,
  const usize        _idx_a,
  const usize        _idx_b
);

/* 
  Insertion
*/

/* copies the new element at the end if the vector*/
DE_CONTAINER_VECTOR_API u0
de_vec_push_back(
  de_vec *const   _vec,
  const u0* const _element
);

/* moves all further elements back, copies the element to a specific index, */
DE_CONTAINER_VECTOR_API u0
de_vec_insert(
  de_vec *const       _vec,
  const usize         _idx,
  const u0* const     _element
);

/* copies the elements to a specific index, moves all further elements back*/
DE_CONTAINER_VECTOR_API u0
de_vec_insert_batch(
  de_vec *const                _vec,
  const usize                  _idx,
  const u0 *const              _elements,
  const usize                  _amount
);

/* appends _src to _dst (destroys _src) */
DE_CONTAINER_VECTOR_API u0
de_vec_concat(
  de_vec *const                _dst,
  de_vec *const                _src
);

/* appends _src to _dst (copy), does not deepcopy elements (only copies raw data) */
DE_CONTAINER_VECTOR_API u0
de_vec_concat_keep(
  de_vec *const                _dst,
  de_vec *const                _src
);

/* 
  removing
*/

/* remove last element. */
DE_CONTAINER_VECTOR_API u0
de_vec_pop_back(
  de_vec *const _vec
);
/* remove last element. */
DE_CONTAINER_VECTOR_API u0
de_vec_pop_back_with_destructor(
  de_vec *const _vec
);


/* remove last element. doesnt destroy the last element, but instead moves it to _element
   requires _element to be allocated enough memory */
DE_CONTAINER_VECTOR_API u0
de_vec_pop_back_keep(
  de_vec *const       _vec,
  u0 *                _element
);

/* remove element at position _idx, moves subsequent elements forwards by one (slow) */
DE_CONTAINER_VECTOR_API u0
de_vec_erase(
  de_vec *const       _vec,
  const usize         _idx
);

/* remove n elements at position _idx, moves subsequent elements forwards by _amount */
DE_CONTAINER_VECTOR_API u0
de_vec_erase_batch(
  de_vec *const         _vec,
  const usize           _idx,
  const usize           _amount
);

/* remove by value (first occurrence), returns true if removed */
DE_CONTAINER_VECTOR_API bool
de_vec_remove(
  de_vec *const           _vec,
  const u0 *const         _value,
  de_vec_cmp_func         _cmp   /* comparator: returns 0 when equal */
);

/* remove by value, returns amount of removed */
DE_CONTAINER_VECTOR_API usize
de_vec_remove_all(
  de_vec *const           _vec,
  const u0 *const         _value,
  de_vec_cmp_func         _cmp   /* comparator: returns 0 when equal */
);

/* 
  algorithms
*/

/* returns address to (first) element that _pred returns true. If no element matches return de_vec_info_raw_data_end */
DE_CONTAINER_VECTOR_API u0*
de_vec_find(
  de_vec *const           _vec,
  de_vec_pred_func        _pred,
  u0 *                    _data
);

/* executes the provided function on all elements*/
DE_CONTAINER_VECTOR_API u0
de_vec_foreach(
  de_vec *const           _vec,
  de_vec_foreach_func     _cb,
  u0 *                    _data
);

/* executes the provided function on all elements in range */
DE_CONTAINER_VECTOR_API u0
de_vec_foreach_range(
  de_vec *const           _vec,
  de_vec_foreach_func     _cb,
  u0 *                    _data,
  const usize             _start_idx,
  const usize             _end_idx
);

/* sorts the vector based on the provided search function*/
DE_CONTAINER_VECTOR_API u0
de_vec_sort(
  de_vec *const           _vec,
  de_vec_cmp_func         _cmp
);

/* sorts the vector based on the provided search function in the provided range*/
DE_CONTAINER_VECTOR_API u0
de_vec_sort_range(
  de_vec *const           _vec,
  de_vec_cmp_func         _cmp,
  const usize             _start_idx,
  const usize             _end_idx
);

/* reverses the vector */
DE_CONTAINER_VECTOR_API u0
de_vec_reverse(
  de_vec *const           _vec
);

/* 
   swap and unpack 
*/

DE_CONTAINER_VECTOR_API u0
de_vec_swap(
  de_vec *const           _a,
  de_vec *const           _b
);

/* 
  copy vector contents into user buffer; copies (count < de_vec_info_size(_vec) ? _count : de_vec_info_size(_vec)) items
*/
DE_CONTAINER_VECTOR_API u0
de_vec_to_array(
  de_vec *const           _vec,
  const usize             _start_idx,
  u0 *const               _out_buffer,
  const usize             _count
);

/* clang-format on */
#ifdef __cplusplus
} // extern "C"
#endif

#endif

// #define DE_CONTAINER_VECTOR_IMPLEMENTATION_DEVELOPMENT
#if defined(DE_CONTAINER_VECTOR_IMPLEMENTATION) ||                             \
    defined(DE_CONTAINER_VECTOR_IMPLEMENTATION_DEVELOPMENT)
#ifndef DE_CONTAINER_VECTOR_IMPLEMENTATION_INTERNAL
#define DE_CONTAINER_VECTOR_IMPLEMENTATION_INTERNAL
#ifdef __cplusplus
extern "C" {
#endif

/* implementations */
#include <assert.h>
#include <common.h>
#include <stdlib.h>
#include <string.h>

/* macro defines */
#ifndef DE_OPTIONS_VECTOR_DEFAULT_DESTRUCTOR
void DE_OPTIONS_VECTOR_DEFAULT_DESTRUCTOR_brrrrr(__attribute__((__unused__))
                                                 u0 *const data) {}
#define DE_OPTIONS_VECTOR_DEFAULT_DESTRUCTOR                                   \
  DE_OPTIONS_VECTOR_DEFAULT_DESTRUCTOR_brrrrr
#endif

#ifndef DE_OPTIONS_VECTOR_INITIAL_SIZE
#define DE_OPTIONS_VECTOR_INITIAL_SIZE 16
#endif

#ifndef DE_OPTIONS_VECTOR_GROWTH_FACTOR
#define DE_OPTIONS_VECTOR_GROWTH_FACTOR 2
#endif

#ifndef DE_OPTIONS_VECTOR_DATA_PTR_MALLOC_FUNCTION
#define DE_OPTIONS_VECTOR_DATA_PTR_MALLOC_FUNCTION malloc
#endif

#ifndef DE_OPTIONS_VECTOR_DATA_PTR_FREE_FUNCTION
#define DE_OPTIONS_VECTOR_DATA_PTR_FREE_FUNCTION free
#endif

DE_CONTAINER_VECTOR_INTERNAL usize _next_power_of_2(usize x) {
  if (x == 0)
    return 1;
  x--;
  x |= x >> 1;
  x |= x >> 2;
  x |= x >> 4;
  x |= x >> 8;
  x |= x >> 16;
  x |= x >> 32;
  x++;
  return x;
}

#define DE_C_VEC_D_MALLOC DE_OPTIONS_VECTOR_DATA_PTR_MALLOC_FUNCTION
#define DE_C_VEC_D_FREE DE_OPTIONS_VECTOR_DATA_PTR_FREE_FUNCTION
#define DE_C_VEC_MEMCPY memcpy
#define DE_C_VEC_MEMMOV memmove
#define DE_C_VEC_MEMCMP memcmp
#define DE_C_VEC_MEMSET memset
#define DE_C_VEC_ASSERT assert
/*
  constructors
*/

DE_CONTAINER_VECTOR_INTERNAL de_vec de_vec_create(const usize _item_size) {
  return (de_vec){
      _item_size, DE_OPTIONS_VECTOR_INITIAL_SIZE, 0,
      DE_C_VEC_D_MALLOC(DE_OPTIONS_VECTOR_INITIAL_SIZE * _item_size),
      DE_OPTIONS_VECTOR_DEFAULT_DESTRUCTOR};
}

DE_CONTAINER_VECTOR_INTERNAL de_vec
de_vec_create_with_capacity(const usize _item_size, usize _initial_capacity) {
  _initial_capacity = _next_power_of_2(_initial_capacity);
  return (de_vec){_item_size, _initial_capacity, 0,
                  DE_C_VEC_D_MALLOC(_initial_capacity * _item_size),
                  DE_OPTIONS_VECTOR_DEFAULT_DESTRUCTOR};
}

DE_CONTAINER_VECTOR_INTERNAL de_vec de_vec_create_verbose(
    const usize _item_size, const de_vec_destructor_func _destructor_function) {
  return (de_vec){
      _item_size, DE_OPTIONS_VECTOR_INITIAL_SIZE, 0,
      DE_C_VEC_D_MALLOC(DE_OPTIONS_VECTOR_INITIAL_SIZE * _item_size),
      _destructor_function};
}

DE_CONTAINER_VECTOR_INTERNAL de_vec de_vec_create_with_capacity_verbose(
    const usize _item_size, usize _initial_capacity,
    const de_vec_destructor_func _destructor_function) {
  _initial_capacity = _next_power_of_2(_initial_capacity);
  return (de_vec){_item_size, _initial_capacity, 0,
                  DE_OPTIONS_VECTOR_DATA_PTR_MALLOC_FUNCTION(_initial_capacity *
                                                             _item_size),
                  _destructor_function};
}

/* initialize from existing contiguous vector  */
DE_CONTAINER_VECTOR_INTERNAL de_vec de_vec_create_from_array(
    const usize _item_size, const u0 *_data, const usize _count) {
  de_vec out = de_vec_create_with_capacity(_item_size, _count);
  DE_C_VEC_MEMCPY(out.data, _data, _count * _item_size);
  out.used = _count;
  return out;
}

/* copies raw data from vector */
DE_CONTAINER_VECTOR_INTERNAL de_vec
de_vec_create_from_vector(const de_vec *const _src) {
  de_vec out = *_src;
  usize bytes = _src->item_size * _src->used;
  out.data = DE_C_VEC_D_MALLOC(bytes);
  DE_C_VEC_MEMCPY(out.data, _src->data, bytes);
  return out;
}

DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_clear(de_vec *const _vec) {
  _vec->used = 0;
}

/* call element destroyer on each item, but keep capacity*/
DE_CONTAINER_VECTOR_INTERNAL u0
de_vec_clear_with_destructor(de_vec *const _vec) {
  const de_vec_destructor_func f = _vec->destructor;
  DE_C_VEC_VOID_REPLACEMENT *data = _vec->data;
  const usize item_size = _vec->item_size;
  const DE_C_VEC_VOID_REPLACEMENT *data_end = data + item_size * _vec->used;
  while (data != data_end) {
    f(data);
    data += item_size;
  }
  _vec->used = 0;
}

/* delete entire vector */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_delete(de_vec *const _vec) {
  DE_C_VEC_D_FREE(_vec->data);
  *_vec = (de_vec){0};
}

DE_CONTAINER_VECTOR_INTERNAL u0
de_vec_delete_with_destructor(de_vec *const _vec) {
  de_vec_clear_with_destructor(_vec);
  DE_C_VEC_D_FREE(_vec->data);
  *_vec = (de_vec){0};
}

/* set or replace element destructor function */
DE_CONTAINER_VECTOR_INTERNAL u0
de_vec_set_destructor(de_vec *const _vec, de_vec_destructor_func _destructor) {
  _vec->destructor = _destructor;
}

/*
  Info getters
*/

DE_CONTAINER_VECTOR_INTERNAL usize de_vec_info_item_size(de_vec *const _vec) {
  return _vec->item_size;
}

/* current number of stored elements */
DE_CONTAINER_VECTOR_INTERNAL usize de_vec_info_size(de_vec *const _vec) {
  return _vec->used;
}

/* underlying allocated capacity in elements */
DE_CONTAINER_VECTOR_INTERNAL usize de_vec_info_capacity(de_vec *const _vec) {
  return _vec->capacity;
}

/* raw data pointer (start) */
DE_CONTAINER_VECTOR_INTERNAL u0 *de_vec_info_raw_data(de_vec *const _vec) {
  return _vec->data;
}

/* raw data pointer (one-past-end of used elements) */
DE_CONTAINER_VECTOR_INTERNAL u0 *de_vec_info_raw_data_end(de_vec *const _vec) {
  return (u0 *)(_vec->data + _vec->used * _vec->item_size);
}

DE_CONTAINER_VECTOR_INTERNAL bool de_vec_info_empty(de_vec *const _vec) {
  return _vec->used == 0;
}

/*
  Capacity / resizing
*/

/* reserves up to size, will not shrink/loose data */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_reserve(de_vec *const _vec,
                                               usize _size) {
  _size = _next_power_of_2(_size);
  if (_vec->capacity < _size) {
    void *new_mem = DE_C_VEC_D_MALLOC(_size * _vec->item_size);
    DE_C_VEC_MEMCPY(new_mem, _vec->data, _vec->used * _vec->item_size);
    DE_C_VEC_D_FREE(_vec->data);
    _vec->data = new_mem;
    _vec->capacity = _size;
  }
}

/* shrinks vector, will not delete data*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_shrink_to_fit(de_vec *const _vec) {
  const usize _size = _next_power_of_2(_vec->used);
  if (_size < _vec->capacity) {
    void *new_mem = DE_C_VEC_D_MALLOC(_size * _vec->item_size);
    DE_C_VEC_MEMCPY(new_mem, _vec->data, _vec->used * _vec->item_size);
    DE_C_VEC_D_FREE(_vec->data);
    _vec->data = new_mem;
    _vec->capacity = _size;
  }
}

/* resizes vector, will delete data if necessary */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_resize(de_vec *const _vec,
                                              const usize _new_size) {
  const usize _size = _next_power_of_2(_new_size);
  void *new_mem = DE_C_VEC_D_MALLOC(_size * _vec->item_size);
  if (_size < _vec->used) {
    DE_C_VEC_MEMCPY(new_mem, _vec->data, _new_size * _vec->item_size);
    _vec->used = _new_size;
  } else {
    DE_C_VEC_MEMCPY(new_mem, _vec->data, _vec->used * _vec->item_size);
  }
  DE_C_VEC_D_FREE(_vec->data);
  _vec->data = new_mem;
  _vec->capacity = _size;
}

DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_upsize(de_vec *const _vec) {
  const usize _size = _vec->capacity * DE_OPTIONS_VECTOR_GROWTH_FACTOR;
  void *new_mem = DE_C_VEC_D_MALLOC(_size * _vec->item_size);
  DE_C_VEC_MEMCPY(new_mem, _vec->data, _vec->used * _vec->item_size);
  _vec->capacity = _size;
  DE_C_VEC_D_FREE(_vec->data);
  _vec->data = new_mem;
}

#define de_vec_check_upsize(_vec)                                              \
  if (_vec->used == _vec->capacity) {                                          \
    de_vec_upsize(_vec);                                                       \
  }
#define de_vec_check_upsize_n(_vec, amount)                                    \
  if (_vec->used + amount >= _vec->capacity) {                                 \
    de_vec_reserve(_vec, _vec->used + amount);                                 \
  }
/*
  Element access
*/

/* return address of the element at position _idx*/
DE_CONTAINER_VECTOR_INTERNAL u0 *de_vec_get(de_vec *const _vec,
                                            const usize _idx) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_idx < _vec->used && " has to recieve a valid index");
#endif
  return (u0 *)(_vec->data + _idx * _vec->item_size);
}

/* copies _new_element into the position _idx*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_set(de_vec *const _vec, const usize _idx,
                                           const u0 *const _new_element) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_idx < _vec->used && " has to recieve a valid index");
#endif
  DE_C_VEC_MEMCPY((u0 *)(_vec->data + _idx * _vec->item_size), _new_element,
                  _vec->item_size);
}

/* swaps two elements */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_swap_elements(de_vec *const _vec,
                                                     const usize _idx_a,
                                                     const usize _idx_b) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_idx_a < _vec->used && " has to recieve a valid index");
  DE_C_VEC_ASSERT(_idx_b < _vec->used && " has to recieve a valid index");
#endif
  usize item_size = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *s1 = _vec->data + _idx_a * item_size;
  DE_C_VEC_VOID_REPLACEMENT *s2 = _vec->data + _idx_b * item_size;
  for (usize i = 0; i < item_size; ++i) {
    DE_C_VEC_VOID_REPLACEMENT tmp = s1[i];
    s1[i] = s2[i];
    s2[i] = tmp;
  }
}

/*
  Insertion
*/

/* copies the new element at the end if the vector*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_push_back(de_vec *const _vec,
                                                 const u0 *const _element) {
  de_vec_check_upsize(_vec);
  DE_C_VEC_MEMCPY(_vec->data + _vec->used * _vec->item_size, _element,
                  _vec->item_size);
  ++_vec->used;
}

/* copies the element to a specific index, moves all further elements back*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_insert(de_vec *const _vec,
                                              const usize _idx,
                                              const u0 *const _element) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_idx <= _vec->used && " has to recieve a valid index");
  DE_C_VEC_ASSERT(_element && "Provided element must be valid");
#endif
  de_vec_check_upsize(_vec);

  usize itemsize = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *accesspoint = _vec->data + _idx * itemsize;

  DE_C_VEC_MEMMOV(accesspoint + itemsize, accesspoint,
                  itemsize * (_vec->used - _idx));
  DE_C_VEC_MEMCPY(accesspoint, _element, itemsize);
  ++_vec->used;
}

/* copies the elements to a specific index, moves all further elements back*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_insert_batch(de_vec *const _vec,
                                                    const usize _idx,
                                                    const u0 *const _elements,
                                                    const usize _amount) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_idx <= _vec->used && " has to recieve a valid index");
  DE_C_VEC_ASSERT(_elements && "Provided elements must be valid");
#endif
  de_vec_check_upsize_n(_vec, _amount);
  usize itemsize = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *accesspoint = _vec->data + _idx * itemsize;
  usize amount_size = itemsize * _amount;

  DE_C_VEC_MEMMOV(accesspoint + amount_size, accesspoint,
                  itemsize * (_vec->used - _idx));
  DE_C_VEC_MEMCPY(accesspoint, _elements, amount_size);
  _vec->used += _amount;
}

/* appends _src to _dst (destroys _src) */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_concat(de_vec *const _dst,
                                              de_vec *const _src) {
  de_vec_insert_batch(_dst, _dst->used, _src->data, _src->used);
  de_vec_delete(_src);
}

/* appends _src to _dst (copy) */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_concat_keep(de_vec *const _dst,
                                                   de_vec *const _src) {
  de_vec_insert_batch(_dst, _dst->used, _src->data, _src->used);
}
/*
  removing
*/

/* remove last element. */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_pop_back(de_vec *const _vec) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_vec->used > 0 && "vector has to contain items to pop");
#endif
  --_vec->used;
}

/* remove last element. */
DE_CONTAINER_VECTOR_INTERNAL u0
de_vec_pop_back_with_destructor(de_vec *const _vec) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_vec->used > 0 && "vector has to contain items to pop");
#endif
  _vec->destructor(_vec->data + (_vec->used - 1) * _vec->item_size);
  --_vec->used;
}

/* remove last element. doesnt destroy the last element, but instead moves it to
   _element requires _element to be allocated enough memory */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_pop_back_keep(de_vec *const _vec,
                                                     u0 *_element) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_vec->used > 0 && "vector has to contain items to pop");
#endif
  DE_C_VEC_MEMCPY(_element, _vec->data + (_vec->used - 1) * _vec->item_size,
                  _vec->item_size);
  --_vec->used;
}

/* remove element at position _idx, moves subsequent elements forwards by one
 * (slow) */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_erase(de_vec *const _vec,
                                             const usize _idx) {

#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_idx < _vec->used && " has to recieve a valid index");
#endif
  const usize item_size = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *accesspoint = _vec->data + _idx * item_size;
  DE_C_VEC_MEMMOV(accesspoint, accesspoint + item_size,
                  item_size * (_vec->used - _idx - 1));
  --_vec->used;
}

/* remove n elements at position _idx, moves subsequent elements forwards by
 * _amount */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_erase_batch(de_vec *const _vec,
                                                   const usize _idx,
                                                   const usize _amount) {

#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_idx < _vec->used && " has to recieve a valid index");
  DE_C_VEC_ASSERT((_idx + _amount) <= _vec->used &&
                  "has to delete a valid amount of elements");
#endif
  const usize item_size = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *accesspoint = _vec->data + _idx * item_size;
  DE_C_VEC_MEMMOV(accesspoint, accesspoint + item_size * _amount,
                  item_size * (_vec->used - _idx - _amount));
  _vec->used -= _amount;
}

/* remove by value (first occurrence), returns true if removed
 */
DE_CONTAINER_VECTOR_INTERNAL bool
de_vec_remove(de_vec *const _vec, const u0 *const _value,
              de_vec_cmp_func _cmp /* comparator: returns 0 when equal */) {
  const usize itemsize = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *data = _vec->data;
  DE_C_VEC_VOID_REPLACEMENT *data_end = _vec->data + itemsize * _vec->used;

  for (usize idx = 0; data != data_end; ++idx, data += itemsize) {
    /* comparator returns 0 when equal */
    if (_cmp(data, _value) == 0) {
      de_vec_erase(_vec, idx);
      return true;
    }
  }
  return false;
}

/* remove by value, returns amount of removed */
DE_CONTAINER_VECTOR_INTERNAL usize de_vec_remove_all(
    de_vec *const _vec, const u0 *const _value,
    de_vec_cmp_func _cmp /* comparator: returns 0 when equal */
) {
  const usize itemsize = _vec->item_size;
  /*
  DE_C_VEC_VOID_REPLACEMENT *data = _vec->data;
  const DE_C_VEC_VOID_REPLACEMENT *data_end =
  _vec->data + itemsize * _vec->used;
  */

  usize removed_amount = 0;
  usize i = 0;
  while (i < _vec->used) {
    u0 *item = de_vec_get(_vec, i);
    if (_cmp(item, _value) == 0) {
      de_vec_erase(_vec, i);
      ++removed_amount;
      // do NOT increment i — new item at i must be checked
    } else {
      ++i;
    }
  }

  return removed_amount;
}

/*
  algorithms
*/

/* returns address to (first) element that _pred returns true. If no element
 * matches return de_vec_info_raw_data_end */
DE_CONTAINER_VECTOR_INTERNAL u0 *
de_vec_find(de_vec *const _vec, de_vec_pred_func _pred, u0 *_data) {
  const usize itemsize = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *data = _vec->data;
  const DE_C_VEC_VOID_REPLACEMENT *data_end =
      _vec->data + itemsize * _vec->used;

  while (data != data_end) {
    if (_pred(data, _data))
      return (u0 *)data;
    data += itemsize;
  }
  return (u0 *)data_end;
}

/* executes the provided function on all elements*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_foreach(de_vec *const _vec,
                                               de_vec_foreach_func _cb,
                                               u0 *_data) {
  const usize itemsize = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *data = _vec->data;
  const DE_C_VEC_VOID_REPLACEMENT *data_end =
      _vec->data + itemsize * _vec->used;

  while (data != data_end) {
    _cb(data, _data);
    data += itemsize;
  }
}

/* executes the provided function on all elements in range */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_foreach_range(de_vec *const _vec,
                                                     de_vec_foreach_func _cb,
                                                     u0 *_data,
                                                     const usize _start_idx,
                                                     const usize _end_idx) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_start_idx < _vec->used && " has to recieve a valid index");
  DE_C_VEC_ASSERT(_end_idx < _vec->used && " has to recieve a valid index");
#endif
  const usize itemsize = _vec->item_size;
  DE_C_VEC_VOID_REPLACEMENT *data = _vec->data + _start_idx * itemsize;
  const DE_C_VEC_VOID_REPLACEMENT *data_end = _vec->data + itemsize * _end_idx;

  while (data != data_end) {
    _cb(data, _data);
    data += itemsize;
  }
}

/* sorts the vector based on the provided search function*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_sort(de_vec *const _vec,
                                            de_vec_cmp_func _cmp) {
  qsort(_vec->data, _vec->used, _vec->item_size, _cmp);
}

/* sorts the vector based on the provided search function in the provided
 * range*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_sort_range(de_vec *const _vec,
                                                  de_vec_cmp_func _cmp,
                                                  const usize _start_idx,
                                                  const usize _end_idx) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_start_idx < _vec->used && " has to recieve a valid index");
  DE_C_VEC_ASSERT(_end_idx < _vec->used && " has to recieve a valid index");
#endif
  usize item_size = _vec->item_size;
  qsort(_vec->data + item_size * _start_idx, _end_idx - _start_idx, item_size,
        _cmp);
}

/* reverses the vector */
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_reverse(de_vec *const _vec) {
  usize used = _vec->used;
  if (used <= 1)
    return;

  usize item_size = _vec->item_size;

  for (usize i = 0; i < used / 2; ++i) {
    DE_C_VEC_VOID_REPLACEMENT *s1 = _vec->data + i * item_size;
    DE_C_VEC_VOID_REPLACEMENT *s2 = _vec->data + (used - 1 - i) * item_size;
    for (usize j = 0; j < item_size; ++j) {
      DE_C_VEC_VOID_REPLACEMENT tmp = s1[j];
      s1[j] = s2[j];
      s2[j] = tmp;
    }
  }
}

/*
   swap and unpack
*/

DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_swap(de_vec *const _a,
                                            de_vec *const _b) {
  de_vec tmp = *_a;
  *_a = *_b;
  *_b = tmp;
}

/*
  copy vector contents into user buffer; copies (count < de_vec_info_size(_vec)
  ? _count : de_vec_info_size(_vec)) items
*/
DE_CONTAINER_VECTOR_INTERNAL u0 de_vec_to_array(de_vec *const _vec,
                                                const usize _start_idx,
                                                u0 *const _out_buffer,
                                                const usize _count) {
#ifndef DE_OPTIONS_VECTOR_NO_SAFETY_ASSERTS
  DE_C_VEC_ASSERT(_start_idx < _vec->used && " has to recieve a valid index");
  DE_C_VEC_ASSERT(_start_idx + _count <= _vec->used &&
                  " has to recieve a valid index");
#endif
  memcpy(_out_buffer, _vec->data + _start_idx * _vec->item_size,
         _vec->item_size * _count);
}

#ifdef __cplusplus
} // extern "C"
#endif
#endif
#endif
