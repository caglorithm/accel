# SETTINGS
# --------------------
VERBOSE_OUTPUT = True
STIMULUS_ACTIVE = False

# I2C addresses of connected devices.
# Determine the addresses using sudo i2cdetect -y 1
I2C_OLED_ADDR = 0x3C
I2C_ACCEL_ADDR = 0x1D
ACCELEROMETER_ACTIVITY_THRESHOLD = 12.5

# oled display
OLED_DISPLAY = True

# Logging parameters
LOGGING = True # log activity at all

LOG_TO_REDIS = False
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

LOG_TO_HDF = True
HDF_FILE = 'log.h5'

# SLEEP DETECTION ALGO PARAMETERS
# --------------------
LOGGER_MIN_DELAY = 2.0
LOGGER_MAX_DELAY = 200.0

# Adaptive delay parameters
DELAY_DIVIDE_BY = 10 
DELAY_MULTIPLY_WITH = 1.2

# Activity integrator parameters
ACTIVITY_DECAY_CONSTANT = 2 * 60 * 1000.0 # for use: 2 * 60 * 1000.0, for testing: 10 * 1000.0 #
ACTIVITY_SPIKE_STRENGTH = 0.05 # increase activity by this value for each movement spike
ACTIVITY_DECAY_DELAY = 5 * 60 * 1000.0 # for use: 5 * 60 * 1000.0, for testing: 2 * 1000.0
ACTIVITY_LOWER_BOUND = 1e-3 # stop decay below this value

# Sleep stage detection parameters
ACTIVITY_THRESHOLD_DEEP_SLEEP = 0.01
ACTIVITY_THRESHOLD_WAKE = 0.7

SLEEP_STATE_WAKE = 0
SLEEP_STATE_LIGHT = 1
SLEEP_STATE_DEEP = 2