#include "board.h"
#include "FreeRTOS.h"
#include "SEGGER_SYSVIEW.h"
#include "timestamp.h"
#include "demo.h"

extern const SEGGER_SYSVIEW_OS_API SYSVIEW_X_OS_TraceAPI;
volatile uint32_t traceReady;

static void send_system_description(void)
{
    SEGGER_SYSVIEW_SendSysDesc("N=WeAct G030 Demo,D=Cortex-M0+,O=FreeRTOS");
    SEGGER_SYSVIEW_SendSysDesc("I#15=SysTick,I#38=TIM17");
    SEGGER_SYSVIEW_NameMarker(1, "LED toggle");
    SEGGER_SYSVIEW_NameMarker(2, "Work burst");
}

void SEGGER_SYSVIEW_Conf(void)
{
    trace_timestamp_init();
    SEGGER_SYSVIEW_Init(1000000u, SystemCoreClock, &SYSVIEW_X_OS_TraceAPI,
                       send_system_description);
    SEGGER_SYSVIEW_SetRAMBase(0x20000000u);
    traceReady = 1;
}
