/* GNU assembler startup for STM32G030F6P6 (Cortex-M0+). */
.syntax unified
.cpu cortex-m0plus
.thumb

.section .isr_vector,"a",%progbits
.balign 256
.global g_pfnVectors
.type g_pfnVectors, %object
g_pfnVectors:
  .word _estack
  .word Reset_Handler
  .word NMI_Handler
  .word HardFault_Handler
  .word 0
  .word 0
  .word 0
  .word 0
  .word 0
  .word 0
  .word 0
  .word SVC_Handler
  .word 0
  .word 0
  .word PendSV_Handler
  .word SysTick_Handler
  .word WWDG_IRQHandler
  .word 0
  .word RTC_TAMP_IRQHandler
  .word FLASH_IRQHandler
  .word RCC_IRQHandler
  .word EXTI0_1_IRQHandler
  .word EXTI2_3_IRQHandler
  .word EXTI4_15_IRQHandler
  .word 0
  .word DMA1_Channel1_IRQHandler
  .word DMA1_Channel2_3_IRQHandler
  .word DMA1_Ch4_5_DMAMUX1_OVR_IRQHandler
  .word ADC1_IRQHandler
  .word TIM1_BRK_UP_TRG_COM_IRQHandler
  .word TIM1_CC_IRQHandler
  .word 0
  .word TIM3_IRQHandler
  .word 0
  .word 0
  .word TIM14_IRQHandler
  .word 0
  .word TIM16_IRQHandler
  .word TIM17_IRQHandler
  .word I2C1_IRQHandler
  .word I2C2_IRQHandler
  .word SPI1_IRQHandler
  .word SPI2_IRQHandler
  .word USART1_IRQHandler
  .word USART2_IRQHandler
  .word 0
.size g_pfnVectors, .-g_pfnVectors

.section .text.Reset_Handler,"ax",%progbits
.global Reset_Handler
.type Reset_Handler, %function
.thumb_func
Reset_Handler:
    /* Initialize C storage before calling any C code. */
    ldr r0, =_sidata
    ldr r1, =_sdata
    ldr r2, =_edata
1:
    cmp r1, r2
    bcs 2f
    ldr r3, [r0]
    str r3, [r1]
    adds r0, #4
    adds r1, #4
    b 1b
2:
    ldr r1, =_sbss
    ldr r2, =_ebss
    movs r3, #0
3:
    cmp r1, r2
    bcs 4f
    str r3, [r1]
    adds r1, #4
    b 3b
4:
    bl SystemInit
    bl __libc_init_array
    bl main
5:
    b 5b
.size Reset_Handler, .-Reset_Handler

.section .text.Default_Handler,"ax",%progbits
.global Default_Handler
.type Default_Handler, %function
.thumb_func
Default_Handler:
    b .
.size Default_Handler, .-Default_Handler

/* Newlib's initialization hook; this C-only experiment needs no extra setup. */
.section .text._init,"ax",%progbits
.global _init
.type _init, %function
.thumb_func
_init:
    bx lr
.size _init, .-_init

.macro weak_handler name
    .weak \name
    .thumb_set \name, Default_Handler
.endm

weak_handler NMI_Handler
weak_handler HardFault_Handler
weak_handler SVC_Handler
weak_handler PendSV_Handler
weak_handler SysTick_Handler
weak_handler WWDG_IRQHandler
weak_handler RTC_TAMP_IRQHandler
weak_handler FLASH_IRQHandler
weak_handler RCC_IRQHandler
weak_handler EXTI0_1_IRQHandler
weak_handler EXTI2_3_IRQHandler
weak_handler EXTI4_15_IRQHandler
weak_handler DMA1_Channel1_IRQHandler
weak_handler DMA1_Channel2_3_IRQHandler
weak_handler DMA1_Ch4_5_DMAMUX1_OVR_IRQHandler
weak_handler ADC1_IRQHandler
weak_handler TIM1_BRK_UP_TRG_COM_IRQHandler
weak_handler TIM1_CC_IRQHandler
weak_handler TIM3_IRQHandler
weak_handler TIM14_IRQHandler
weak_handler TIM16_IRQHandler
weak_handler TIM17_IRQHandler
weak_handler I2C1_IRQHandler
weak_handler I2C2_IRQHandler
weak_handler SPI1_IRQHandler
weak_handler SPI2_IRQHandler
weak_handler USART1_IRQHandler
weak_handler USART2_IRQHandler
