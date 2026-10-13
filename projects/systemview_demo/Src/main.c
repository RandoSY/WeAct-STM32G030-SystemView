#include "board.h"
#include "FreeRTOS.h"
#include "task.h"
#include "demo.h"
#include "SEGGER_RTT.h"

int main(void)
{
    if (HAL_Init() != HAL_OK) board_fatal(4);
    SystemClock_Config();
    board_gpio_init();
    SEGGER_SYSVIEW_Conf();
    configASSERT(DEMO_LED_PERIOD_MS > 0 && DEMO_WORK_PERIOD_MS > 0);
    configASSERT(xTaskCreate(StartLEDtask, "LEDtask", DEMO_LED_STACK_WORDS,
                            NULL, 1, NULL) == pdPASS);
    configASSERT(xTaskCreate(StartWorkTask, "WorkTask", DEMO_WORK_STACK_WORDS,
                            NULL, 2, NULL) == pdPASS);
    SEGGER_RTT_WriteString(0, "WeAct G030 trace demo: boot\n");
    /* The recorder starts SystemView via RTT channel 1. No host is needed
       for the LED/work tasks to run; unconsumed console output is dropped. */
    vTaskStartScheduler();
    board_fatal(7);
}
