import smbus
import time
# Get I2C bus
bus = smbus.SMBus(1)
# I2C address of the device
MMA8452Q_DEFAULT_ADDRESS = 0x1D
# MMA8452Q Register Map
MMA8452Q_REG_STATUS = 0x00 # Data status Register
MMA8452Q_REG_OUT_X_MSB = 0x01 # Output Value X MSB
MMA8452Q_REG_OUT_X_LSB = 0x02 # Output Value X LSB
MMA8452Q_REG_OUT_Y_MSB = 0x03 # Output Value Y MSB
MMA8452Q_REG_OUT_Y_LSB = 0x04 # Output Value Y LSB
MMA8452Q_REG_OUT_Z_MSB = 0x05 # Output Value Z MSB
MMA8452Q_REG_OUT_Z_LSB = 0x06 # Output Value Z LSB
MMA8452Q_REG_SYSMOD = 0x0B # System mode Register
MMA8452Q_REG_INT_SOURCE = 0x0C # System Interrupt Status Register
MMA8452Q_REG_WHO_AM_I = 0x0D # Device ID Register
MMA8452Q_REG_XYZ_DATA_CFG = 0x0E # Data Configuration Register
MMA8452Q_REG_CTRL_REG1 = 0x2A # Control Register 1
MMA8452Q_REG_CTRL_REG2 = 0x2B # Control Register 2
MMA8452Q_REG_CTRL_REG3 = 0x2C # Control Register 3
MMA8452Q_REG_CTRL_REG4 = 0x2D # Control Register 4
MMA8452Q_REG_CTRL_REG5 = 0x2E # Control Register 5
# MMA8452Q Data Configuration Register
MMA8452Q_DATA_CFG_HPF_OUT = 0x10 # Output Data High-Pass Filtered
MMA8452Q_DATA_CFG_FS_2 = 0x00 # Full-Scale Range = 2g
MMA8452Q_DATA_CFG_FS_4 = 0x01 # Full-Scale Range = 4g
MMA8452Q_DATA_CFG_FS_8 = 0x02 # Full-Scale Range = 8g
# MMA8452Q Control Register 1
MMA8452Q_ASLP_RATE_50 = 0x00 # Sleep mode rate = 50Hz
MMA8452Q_ASLP_RATE_12_5 = 0x40 # Sleep mode rate = 12.5Hz
MMA8452Q_ASLP_RATE_6_25 = 0x80 # Sleep mode rate = 6.25Hz
MMA8452Q_ASLP_RATE_1_56 = 0xC0 # Sleep mode rate = 1.56Hz
MMA8452Q_ODR_800 = 0x00 # Output Data Rate = 800Hz
MMA8452Q_ODR_400 = 0x08 # Output Data Rate = 400Hz
MMA8452Q_ODR_200 = 0x10 # Output Data Rate = 200Hz
MMA8452Q_ODR_100 = 0x18 # Output Data Rate = 100Hz
MMA8452Q_ODR_50 = 0x20 # Output Data Rate = 50Hz
MMA8452Q_ODR_12_5 = 0x28 # Output Data Rate = 12.5Hz
MMA8452Q_ODR_6_25 = 0x30 # Output Data Rate = 6.25Hz
MMA8452Q_ODR_1_56 = 0x38 # Output Data Rate = 1_56Hz
MMA8452Q_MODE_NORMAL = 0x00 # Normal Mode
MMA8452Q_MODE_REDUCED_NOISE = 0x04 # Reduced Noise Mode
MMA8452Q_MODE_FAST_READ = 0x02 # Fast Read Mode
MMA8452Q_MODE_ACTIVE = 0x01 # Active Mode
MMA8452Q_MODE_STANDBY = 0x00 # Standby Mode
class MMA8452Q():
    def __init__(self):
        self.mode_configuration()
        self.data_configuration()
    def write(self, REGISTER, SETTING):
        print("Writing: {:08b}".format(SETTING))
        bus.write_byte_data(MMA8452Q_DEFAULT_ADDRESS, REGISTER, SETTING)
    def mode_configuration(self, MODE=None):
        """Select the Control Register-1 configuration of the accelerometer from the given provided values"""
        if MODE == None:
            #MODE_CONFIG = (MMA8452Q_ODR_800 | MMA8452Q_MODE_REDUCED_NOISE | MMA8452Q_MODE_NORMAL | MMA8452Q_MODE_ACTIVE)
            MODE_CONFIG = (MMA8452Q_ODR_800 | MMA8452Q_MODE_NORMAL | MMA8452Q_MODE_ACTIVE)
        else:
            MODE_CONFIG = (MODE)
        print("Writing: {:08b}".format(MODE_CONFIG))
        bus.write_byte_data(MMA8452Q_DEFAULT_ADDRESS, MMA8452Q_REG_CTRL_REG1, MODE_CONFIG)
    def data_configuration(self):
        """Select the Data Configuration Register configuration of the accelerometer from the given provided values"""
        DATA_CONFIG = (MMA8452Q_DATA_CFG_FS_2)
        print("Data: {:08b}".format(DATA_CONFIG))
        bus.write_byte_data(MMA8452Q_DEFAULT_ADDRESS, MMA8452Q_REG_XYZ_DATA_CFG, DATA_CONFIG)
    def read_accl(self):
        """Read data back from MMA8452Q_REG_STATUS(0x00), 7 bytes
        Status register, X-Axis MSB, X-Axis LSB, Y-Axis MSB, Y-Axis LSB, Z-Axis MSB, Z-Axis LSB"""
        data = bus.read_i2c_block_data(MMA8452Q_DEFAULT_ADDRESS, MMA8452Q_REG_STATUS, 7)
        # Convert the data
        xAccl = (data[1] * 256 + data[2]) / 16
        if xAccl > 2047 :
            xAccl -= 4096
        yAccl = (data[3] * 256 + data[4]) / 16
        if yAccl > 2047 :
            yAccl -= 4096
        zAccl = (data[5] * 256 + data[6]) / 16
        if zAccl > 2047 :
            zAccl -= 4096
        return {'x' : xAccl, 'y' : yAccl, 'z' : zAccl}