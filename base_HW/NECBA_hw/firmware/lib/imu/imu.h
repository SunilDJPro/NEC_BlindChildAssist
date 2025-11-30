#ifndef IMU_CONFIG_H
#define IMU_CONFIG_H

// include the header of your new driver here similar to default_imu.h
#include "default_imu.h"


#ifdef USE_MPU9150_IMU
    #define IMU MPU9150IMU
#endif

#ifdef USE_MPU9250_IMU
    #define IMU MPU9250IMU
#endif

#ifdef USE_FAKE_IMU
    #define IMU FakeIMU
#endif

#endif

