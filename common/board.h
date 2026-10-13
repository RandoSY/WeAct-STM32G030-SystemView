#ifndef WEACT_G030_BOARD_H
#define WEACT_G030_BOARD_H
#include "stm32g0xx_hal.h"

/* WeAct core board v1.0 schematic: LED anode goes to 3V3; PA4 sinks it. */
#define USER_LED_Pin GPIO_PIN_4
#define USER_LED_GPIO_Port GPIOA
extern volatile uint32_t boardFailure;
void SystemClock_Config(void);
void board_gpio_init(void);
void board_led_toggle(void);
void board_fatal(uint32_t reason);
#endif
