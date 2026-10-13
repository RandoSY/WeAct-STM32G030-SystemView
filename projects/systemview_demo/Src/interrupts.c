#include "board.h"
#include "demo.h"
#include "SEGGER_SYSVIEW.h"
void xPortSysTickHandler(void);

void SysTick_Handler(void) { xPortSysTickHandler(); }
void NMI_Handler(void) { board_fatal(5); }
void HardFault_Handler(void) { board_fatal(6); }

void TIM17_IRQHandler(void)
{
    if (traceReady) SEGGER_SYSVIEW_RecordEnterISR();
    if (TIM17->SR & TIM_SR_UIF) {
        TIM17->SR = ~TIM_SR_UIF;
        HAL_IncTick();
    }
    if (traceReady) SEGGER_SYSVIEW_RecordExitISR();
}
