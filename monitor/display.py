from machine import Pin, I2C
import monitor.icons as icons
import ssd1306

BOX_TOP     = 5
BOX_LEFT    = 10
BOX_WIDTH   = 108
BOX_HIGHT   = 25 
SHIFT       = 10

class Display(object):

    def __init__(self):
        self._display = self._create_display()

    def _create_display(self):
        i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
        return ssd1306.SSD1306_I2C(128, 64, i2c)

    def clear(self):
        self._display.fill(0)
                
    def set_source_display(self, on_grid):
        self.clear()

        shift = 0 if on_grid else SHIFT
        self._display.rect(BOX_LEFT + shift, BOX_TOP, BOX_WIDTH - shift, BOX_HIGHT, 1)

        if on_grid:
            self.print_icon(BOX_LEFT + shift + 8, BOX_TOP + 5, icons.GRID)
            self._display.text('Grid', BOX_LEFT + shift + 40, BOX_TOP + 9, 1)
        else:
            self._display.rect(BOX_LEFT, BOX_TOP + 4, shift, BOX_HIGHT - 7, 1)

        self.print_icon(BOX_LEFT + 8, 34, icons.BATTERY)
        self.print_icon(BOX_LEFT + 8, 50, icons.CONSUMPTION)
        self._display.show()


    def update_stats_display(self, on_grid, battery_charge, consumption):
        self._display.fill_rect(BOX_LEFT + 30, BOX_TOP + 32, 80, 64 - BOX_TOP, 0)
        self._display.text(str(consumption) + ' W', BOX_LEFT + 30, BOX_TOP + 48, 1)
        self._display.text(str(battery_charge) + ' %',
                           BOX_LEFT + (8 if consumption < 0 else 0) + 30,
                           BOX_TOP + 32, 1)
        self._display.show()

        if not on_grid:
            shift = 0 if on_grid else SHIFT
            self._display.fill_rect(BOX_LEFT + shift  + 2, BOX_TOP + 2,
                                    BOX_WIDTH - shift  - 4, BOX_HIGHT - 4,
                                    0)
            level_start = int((BOX_WIDTH - 4) * (109 - battery_charge) / 100)
            self._display.fill_rect(BOX_LEFT + shift + level_start + 2, BOX_TOP + 2,
                                    BOX_WIDTH - shift - level_start - 4, BOX_HIGHT - 4,
                                    1)
        self._display.show()
        
    def print_icon(self, x, y, icon):
        for l, line in enumerate(icon.split('\n')):
            for c, chr in enumerate(line):
                if chr == '0':
                    self._display.pixel(x + c, y + l - 1, 1)
                else:
                    self._display.pixel(x + c, y + l - 1, 0)

