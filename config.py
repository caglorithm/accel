# I2C addresses of connected devices.
# Determine the addresses using sudo i2cdetect -y 1
I2C_OLED_ADDR = 0x3C
I2C_ACCEL_ADDR = 0x1D

ACCELEROMETER_ACTIVITY_THRESHOLD = 12.5

LOG_TO_REDIS = True
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

LOG_TO_HDF = True
HDF_FILE = 'log.h5'
