#define _GNU_SOURCE
#include <pthread.h>
#include <stdint.h>
#include <sys/resource.h>

/* Match the default worker budget, without assuming the main thread has the
 * worker's explicitly allocated native stack. All supported stacks grow down. */
size_t silk_runtime_main_stack_budget(uintptr_t top) {
  const size_t desired = 4 * 1024 * 1024;
  const size_t reserve = 2 * 1024 * 1024;
  uintptr_t low = 0, high = 0;
#if defined(__APPLE__)
  pthread_t thread = pthread_self();
  high = (uintptr_t)pthread_get_stackaddr_np(thread);
  size_t size = pthread_get_stacksize_np(thread);
  if (size <= high) low = high - size;
  /* pthread's main-stack metadata can exceed a lowered soft resource limit. */
  struct rlimit limit;
  if (getrlimit(RLIMIT_STACK, &limit) == 0 && limit.rlim_cur != RLIM_INFINITY &&
      limit.rlim_cur < size) low = high - (uintptr_t)limit.rlim_cur;
#elif defined(__linux__)
  pthread_attr_t attributes;
  if (pthread_getattr_np(pthread_self(), &attributes) == 0) {
    void *base = 0;
    size_t size = 0;
    if (pthread_attr_getstack(&attributes, &base, &size) == 0) {
      low = (uintptr_t)base;
      high = low + size;
    }
    pthread_attr_destroy(&attributes);
  }
#endif
  /* Keep the engine default if platform stack discovery is unavailable. */
  if (!low || top > high) return 1024 * 1024;
  if (top <= low) return 1;
  size_t available = top - low;
  /* On smaller stacks, keep half for native calls and error recovery. */
  size_t headroom = available / 2 < reserve ? available / 2 : reserve;
  size_t budget = available - headroom;
  /* Zero disables SilkJS's guard, so even a nearly exhausted stack gets one. */
  if (!budget) return 1;
  return budget < desired ? budget : desired;
}
