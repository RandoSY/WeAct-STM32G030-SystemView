#include "timestamp.h"
#include "stm32g0xx_hal.h"

volatile uint32_t timestampHigh;
volatile uint32_t timestampReady;

unsigned int SystemView_GetTimestamp(void)
{
    /* TIM3 is 16-bit on G030. An unserviced overflow must be accounted for
       even inside a SystemView/FreeRTOS critical section. Preserve PRIMASK. */
    uint32_t savedMask = __get_PRIMASK();
    __disable_irq();
    uint32_t high = timestampHigh;
    uint32_t low = TIM3->CNT & 0xffffu;
    if (TIM3->SR & TIM_SR_UIF) {
        high += 0x10000u;
        low = TIM3->CNT & 0xffffu;
    }
    __set_PRIMASK(savedMask);
    return high + low;
}

unsigned int SystemView_GetInterruptId(void)
{
    return __get_IPSR();
}

void trace_timestamp_init(void)
{
    /* APB prescaler is DIV1 in this board setup: timer clock = PCLK1. */
    __HAL_RCC_TIM3_CLK_ENABLE();
    /* Freeze even when attaching without our launch script. A halted CPU
       cannot service wraps; leaving the timer running would lose time. */
    DBG->APBFZ1 |= DBG_APB_FZ1_DBG_TIM3_STOP;
    TIM3->CR1 = 0;
    TIM3->DIER = 0;
    TIM3->PSC = HAL_RCC_GetPCLK1Freq() / 1000000u - 1u;
    TIM3->ARR = 0xffffu;
    TIM3->EGR = TIM_EGR_UG;
    TIM3->SR = 0;
    TIM3->CNT = 0;
    timestampHigh = 0;
    HAL_NVIC_SetPriority(TIM3_IRQn, 0, 0); /* Highest priority; no RTOS calls. */
    HAL_NVIC_ClearPendingIRQ(TIM3_IRQn);
    TIM3->DIER = TIM_DIER_UIE;
    HAL_NVIC_EnableIRQ(TIM3_IRQn);
    timestampReady = 1;
    TIM3->CR1 = TIM_CR1_CEN;
}

void TIM3_IRQHandler(void)
{
    if (TIM3->SR & TIM_SR_UIF) {
        TIM3->SR = ~TIM_SR_UIF;
        timestampHigh += 0x10000u;
    }
    /* The extension interrupt is intentionally not traced, avoiding trace
       calls from the timestamp source itself. It runs every 65.536 ms.
       Interrupts must not be disabled for an entire 65.536 ms period. */
}
