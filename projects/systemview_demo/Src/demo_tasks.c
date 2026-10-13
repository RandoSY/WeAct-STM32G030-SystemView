#include "board.h"
#include "FreeRTOS.h"
#include "task.h"
#include "demo.h"
#include "timestamp.h"
#include "SEGGER_SYSVIEW.h"
#include "SEGGER_RTT.h"

volatile uint32_t ledIterations, workIterations, workChecksum;
volatile uint32_t ledStackWordsFree, workStackWordsFree, idleStackWordsFree;
volatile uint32_t rtosHeapBytesFree;

void StartLEDtask(void *argument)
{
    (void)argument;
    TickType_t lastWake = xTaskGetTickCount();
    for (;;) {
        SEGGER_SYSVIEW_MarkStart(1);
        board_led_toggle();
        ledIterations++;
        SEGGER_SYSVIEW_MarkStop(1);
        ledStackWordsFree = uxTaskGetStackHighWaterMark(NULL);
        idleStackWordsFree = uxTaskGetStackHighWaterMark(xTaskGetIdleTaskHandle());
        rtosHeapBytesFree = xPortGetFreeHeapSize();
        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(DEMO_LED_PERIOD_MS));
    }
}

void StartWorkTask(void *argument)
{
    (void)argument;
    TickType_t lastWake = xTaskGetTickCount();
    for (;;) {
        SEGGER_SYSVIEW_MarkStart(2);
        uint32_t start = SystemView_GetTimestamp();
        /* An intentionally visible workload: approximately 2 ms of elapsed
           time, including any interrupt preemption, not a CPU-cycle claim. */
        while ((uint32_t)(SystemView_GetTimestamp() - start) < DEMO_WORK_BURST_US)
            workChecksum = workChecksum * 1664525u + 1013904223u;
        workIterations++;
        SEGGER_SYSVIEW_MarkStop(2);
        SEGGER_RTT_WriteString(0, "WorkTask: burst complete\n");
        workStackWordsFree = uxTaskGetStackHighWaterMark(NULL);
        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(DEMO_WORK_PERIOD_MS));
    }
}
