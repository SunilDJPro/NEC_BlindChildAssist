#ifndef MOTOR_H
#define MOTOR_H

// include the header of your new driver here similar to default_motor.h
#include "default_motor.h"

// now you can create a config constant that you can use in lino_base_config.h
#ifdef USE_GENERIC_2_IN_MOTOR_DRIVER
    // pass your built in class to Motor macro
    #define Motor Generic2
#endif

#ifdef USE_GENERIC_1_IN_MOTOR_DRIVER
    // pass your built in class to Motor macro
    #define Motor Generic1
#endif

#ifdef USE_BTS7960_MOTOR_DRIVER
    // pass your built in class to Motor macro
    #define Motor BTS7960
#endif

#ifdef USE_ESC_MOTOR_DRIVER
    // pass your built in class to Motor macro
    #define Motor ESC
#endif


#endif
