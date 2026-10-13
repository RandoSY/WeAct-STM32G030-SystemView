#ifndef WEACT_SYSTEMVIEW_DEMO_H
#define WEACT_SYSTEMVIEW_DEMO_H
#include <stdint.h>

/* Edit only these values for the first timing experiments. */
#define DEMO_LED_PERIOD_MS 200u
#define DEMO_WORK_PERIOD_MS 500u
#define DEMO_WORK_BURST_US 2000u
#define DEMO_LED_STACK_WORDS 192u
#define DEMO_WORK_STACK_WORDS 256u

extern volatile uint32_t ledIterations, workIterations, workChecksum;
extern volatile uint32_t ledStackWordsFree, workStackWordsFree, idleStackWordsFree;
extern volatile uint32_t rtosHeapBytesFree, rtosFailure, traceReady;
void StartLEDtask(void *argument);
void StartWorkTask(void *argument);
void SEGGER_SYSVIEW_Conf(void);
#endif
