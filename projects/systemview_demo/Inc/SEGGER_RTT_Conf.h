#ifndef SEGGER_RTT_CONF_H
#define SEGGER_RTT_CONF_H
/* Channel 0 is a nonblocking status console; channel 1 is reserved for SystemView/yapicoprobe. */
#define SEGGER_RTT_MAX_NUM_UP_BUFFERS 2
#define SEGGER_RTT_MAX_NUM_DOWN_BUFFERS 2
#define BUFFER_SIZE_UP 128
#define BUFFER_SIZE_DOWN 8
/* Cortex-M0: save/restore PRIMASK, including nested calls and ISR callers. */
#define SEGGER_RTT_LOCK() { unsigned int rtt_saved_primask; \
    __asm volatile ("mrs %0, primask\n cpsid i" : "=r" (rtt_saved_primask) :: "memory")
#define SEGGER_RTT_UNLOCK() \
    __asm volatile ("msr primask, %0" :: "r" (rtt_saved_primask) : "memory"); }
#endif
