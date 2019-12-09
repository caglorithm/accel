import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

import config

class OLED:
    def __init__(self):
        OLED_RESET = digitalio.DigitalInOut(board.D4)
        self.WIDTH = 128
        self.HEIGHT = 32 

        self.i2c = board.I2C()
        self.oled = adafruit_ssd1306.SSD1306_I2C(self.WIDTH, self.HEIGHT, \
                                                 self.i2c, addr=config.I2C_OLED_ADDR, reset=OLED_RESET)
        self.oled.fill(0)
        self.oled.show()
        self.image = Image.new('1', (self.oled.width, self.oled.height))
        self.draw = ImageDraw.Draw(self.image)
        
        self.font = ImageFont.load_default()
        self.small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
        self.medium_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
        self.large_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        
        self.draw_text("Sleep Well", clear_display = True, draw_frame = 1, font='large')        
        self.draw_image()
    def clear_display(self, redraw=False):
        self.draw.rectangle((0, 0, self.oled.width, self.oled.height * 2), outline=0, fill=0)
        if redraw:
            self.draw_image()
    def draw_image(self):
        self.oled.image(self.image)
        self.oled.show()   
        
    def draw_text(self, text, clear_display = False, font=None, pos='center', \
                  draw_frame = None, redraw = False):
        # clear display
        if clear_display:
            self.clear_display()
        if font is None:
            font = self.font
        elif font == "large":
            font = self.large_font
        elif font == "medium":
            font = self.medium_font            
        elif font == "small":
            font = self.small_font
            
        if draw_frame is not None:
            self.draw_frame(border = draw_frame)
            
        text_width, text_height = self.draw.textsize(text, font=font)
        if pos == 'center':
            self.draw.text((self.oled.width//2 - text_width//2, self.oled.height//2 - text_height//2),
                  text, font=font, fill=255)
        elif pos == 'topright':
            self.draw.text((self.oled.width - text_width - 4, 1),
                  text, font=font, fill=255)
        if redraw:
            self.draw_image()
     
    def draw_frame(self, border = 1):
        BORDER = border
        self.draw.rectangle((0, 0, self.oled.width, self.oled.height), outline=255, fill=255)
        self.draw.rectangle((BORDER, BORDER, self.oled.width - BORDER - 1, \
                             self.oled.height - BORDER - 1), outline=0, fill=0)        
    
    def draw_timeseries(self, data, text=None, clear_display = True, redraw = True):
        # subsample if data length is n times the display width
        n_data_windows = len(data)//self.WIDTH
        if n_data_windows > 1:
            data = data[::n_data_windows]
            
        # data must be maximum 128 steps long            
        data = data[-self.WIDTH:]
    
        
        if max(data) > 20: # diffs larger than noise:
            data /= max(data)
            data *= self.HEIGHT # scale data to 32 pixels
        else:
            data /= max(data)
            data *= self.HEIGHT / 3 # if just noise, draw low amplitude
        
        if clear_display:
            self.clear_display()
        for x in range(len(data)-1):
            self.draw.line((x, self.HEIGHT - data[x], x+1, self.HEIGHT - data[x+1]), fill=1)
            #self.draw.point((x, self.HEIGHT - data[x]), fill=1)
        if text is not None:
            self.draw_text(text, font=self.small_font, clear_display = False, pos='topright')
        
        if redraw:    
            self.draw_image()

    def draw_display(self, content):
        timeseries = content['timeseries']
        status = content['status']
        trigger = content['trigger']
        
        #self.draw_frame(1)
        self.draw_timeseries(timeseries, text=status, clear_display = True, redraw = False)
        if trigger:
            self.draw_text("STIMULUS", font='medium')
        self.draw_image()