#include "board.h"

int main(void)
{
    if (HAL_Init() != HAL_OK) board_fatal(4);
    SystemClock_Config();
    board_gpio_init();
    for (;;) {
        board_led_toggle();
        HAL_Delay(200);
    }
}

void SysTick_Handler(void) { HAL_IncTick(); }
void NMI_Handler(void) { board_fatal(5); }
void HardFault_Handler(void) { board_fatal(6); }
