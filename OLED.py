import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

class OLED:
    def __init__(self):
        oled_reset = digitalio.DigitalInOut(board.D4)
        self.WIDTH = 128
        self.HEIGHT = 32 

        self.i2c = board.I2C()
        self.oled = adafruit_ssd1306.SSD1306_I2C(self.WIDTH, self.HEIGHT, self.i2c, addr=0x3c, reset=oled_reset)
        self.oled.fill(0)
        self.oled.show()
        self.image = Image.new('1', (self.oled.width, self.oled.height))
        self.draw = ImageDraw.Draw(self.image)
        
        self.font = ImageFont.load_default()
        self.small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
        self.medium_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
        self.large_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        
        self.draw_text("Sleep Well", draw_frame = 1, font='large')        
        
    def clear_display(self, redraw=False):
        self.draw.rectangle((0, 0, self.oled.width, self.oled.height * 2), outline=0, fill=0)
        if redraw:
            self.draw_image()
    def draw_image(self):
        self.oled.image(self.image)
        self.oled.show()   
        
    def draw_text(self, text, clear_display = True, font=None, pos='center', draw_frame = None):
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
            BORDER = draw_frame
            self.draw.rectangle((0, 0, self.oled.width, self.oled.height), outline=255, fill=255)
            self.draw.rectangle((BORDER, BORDER, self.oled.width - BORDER - 1, self.oled.height - BORDER - 1),
               outline=0, fill=0)
            
        text_width, text_height = self.draw.textsize(text, font=font)
        if pos == 'center':
            self.draw.text((self.oled.width//2 - text_width//2, self.oled.height//2 - text_height//2),
                  text, font=font, fill=255)
        elif pos == 'topright':
            self.draw.text((self.oled.width - text_width, 0),
                  text, font=font, fill=255)
        
        self.draw_image()
     
        
    def draw_timeseries(self, data, clear_display = True, text=None):
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
        if text is not None:
            self.draw_text(text, font=self.small_font, clear_display = False, pos='topright')
                
        self.draw_image()