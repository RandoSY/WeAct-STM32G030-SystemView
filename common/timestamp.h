#ifndef WEACT_TRACE_TIMESTAMP_H
#define WEACT_TRACE_TIMESTAMP_H
#include <stdint.h>
extern volatile uint32_t timestampHigh;
extern volatile uint32_t timestampReady;
void trace_timestamp_init(void);
unsigned int SystemView_GetTimestamp(void);
unsigned int SystemView_GetInterruptId(void);
#endif
