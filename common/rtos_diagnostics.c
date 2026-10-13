#include "FreeRTOS.h"
#include "task.h"

const int uxTopUsedPriority __attribute__((used, section(".rodata.openocd"))) =
    configMAX_PRIORITIES - 1;
volatile uint32_t rtosFailure;
volatile uint32_t assertLine;
volatile TaskHandle_t rtosFailedTask;

void demo_assert_failed(unsigned int line)
{
    taskDISABLE_INTERRUPTS();
    assertLine = line;
    rtosFailure = 3;
    for (;;) {}
}

void vApplicationMallocFailedHook(void)
{
    taskDISABLE_INTERRUPTS();
    rtosFailure = 1;
    for (;;) {}
}

void vApplicationStackOverflowHook(TaskHandle_t task, char *name)
{
    (void)name;
    taskDISABLE_INTERRUPTS();
    rtosFailedTask = task;
    rtosFailure = 2;
    for (;;) {}
}
