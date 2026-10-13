#include "board.h"

/* The RTOS owns SysTick. HAL's 1 ms clock uses TIM17 instead. */
HAL_StatusTypeDef HAL_InitTick(uint32_t priority)
{
    uint32_t clock = HAL_RCC_GetPCLK1Freq();
    if (priority >= (1u << __NVIC_PRIO_BITS) || clock < 1000000u) return HAL_ERROR;
    __HAL_RCC_TIM17_CLK_ENABLE();
    DBG->APBFZ2 |= DBG_APB_FZ2_DBG_TIM17_STOP;
    TIM17->CR1 = 0;
    TIM17->DIER = 0;
    TIM17->PSC = clock / 1000000u - 1u;
    TIM17->ARR = 999u;
    TIM17->EGR = TIM_EGR_UG;
    TIM17->SR = 0;
    TIM17->CNT = 0;
    HAL_NVIC_SetPriority(TIM17_IRQn, priority, 0);
    HAL_NVIC_ClearPendingIRQ(TIM17_IRQn);
    TIM17->DIER = TIM_DIER_UIE;
    HAL_NVIC_EnableIRQ(TIM17_IRQn);
    uwTickPrio = priority;
    TIM17->CR1 = TIM_CR1_CEN;
    return HAL_OK;
}

void HAL_SuspendTick(void) { TIM17->DIER &= ~TIM_DIER_UIE; }
void HAL_ResumeTick(void) { TIM17->DIER |= TIM_DIER_UIE; }
