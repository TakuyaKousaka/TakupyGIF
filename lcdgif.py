import sys
import time
import os
import io
import struct
import atexit
from gpiozero import Button
from PIL import Image, ImageDraw, ImageFont
#ST7789
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
#SSD1306
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SPI setup
serial = spi(port=0, device=0, gpio_DC=17, gpio_RST=22, bus_speed_hz=52000000)
serial._spi.mode = 3
device = st7789(serial_interface=serial, width=240, height=240, rotate=3, bgr=True)

# I2C setup
oled_serial = i2c(port=1, address=0x3C)
oled = ssd1306(oled_serial, width=128, height=64)

class OLEDPrint:
    def __init__(self, device, font=None):
        self.device = device
        self.font = font or ImageFont.load_default()
        self.buffer = []

    def print(self, msg):
        msg = str(msg).strip()
        if msg:
            wrapped_lines = self._wrap_text(msg)
            self.buffer.extend(wrapped_lines)

            max_lines = self.device.height // self._line_height()
            self.buffer = self.buffer[-max_lines:]
            self._draw()

    def _wrap_text(self, text):
        max_width = self.device.width - 2  # Add margin to avoid clipping
        lines = []
        words = text.split(" ")

        line = ""
        for word in words:
            # Try adding the word to the line
            test_line = f"{line} {word}".strip() if line else word
            test_width = self.font.getbbox(test_line)[2]

            if test_width <= max_width:
                line = test_line
            else:
                if line:
                    lines.append(line)
                # If word itself is too long, break it manually
                while self.font.getbbox(word)[2] > max_width:
                    for i in range(len(word)):
                        part = word[:i+1]
                        if self.font.getbbox(part)[2] > max_width:
                            lines.append(word[:i])
                            word = word[i:]
                            break
                    else:
                        lines.append(word)
                        word = ""
                line = word
        if line:
            lines.append(line)
        return lines

    def _line_height(self):
        ascent, descent = self.font.getmetrics()
        return ascent + descent + 1  # 1px padding to prevent vertical clipping

    def _draw(self):
        image = Image.new("1", self.device.size)
        draw = ImageDraw.Draw(image)
        y = 0
        for line in self.buffer:
            draw.text((0, y), line, font=self.font, fill=255)
            y += self._line_height()
        self.device.display(image)

def show_loading():
    loading_path = os.path.join(BASE_DIR, "loading.png")
    loading_oled_path = os.path.join(BASE_DIR, "loading_oled.png")
    
    #ST7789
    try:
        loadingpng = Image.open(loading_path).convert("RGB").resize((240, 240))
        device.display(loadingpng)
    except Exception as e:
        print(f"Error loading loading.png: {e}")
        oled_print.print(f"Error loading loading.png: {e}")
        loadingtxt = Image.new("RGB", (240, 240), "black")
        draw = ImageDraw.Draw(loadingtxt)
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font = ImageFont.truetype(font_path, 20)
        except:
            font = ImageFont.load_default()
        text = "Loading GIFs..."
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (240 - (bbox[2] - bbox[0])) // 2
        y = (240 - (bbox[3] - bbox[1])) // 2
        draw.text((x, y), text, fill="white", font=font)
        device.display(loadingtxt)

    #SSD1306
    try:
        oled_image = Image.open(loading_oled_path).convert("1").resize((128, 64))
        oled.display(oled_image)
    except Exception as e:
        print(f"OLED loading image error: {e}")
        oled_print.print(f"OLED loading image error: {e}")

        # fallback text
        fallback = Image.new("1", (128, 64), 0)
        draw = ImageDraw.Draw(fallback)
        font = ImageFont.load_default()
        text = "Loading..."
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (128 - (bbox[2] - bbox[0])) // 2
        y = (64 - (bbox[3] - bbox[1])) // 2
        draw.text((x, y), text, font=font, fill=255)
        oled.display(fallback)

def show_shutdown():
        loadingtxt = Image.new("RGB", (240, 240), "black")
        draw = ImageDraw.Draw(loadingtxt)

        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font = ImageFont.truetype(font_path, 20)
        except:
            font = ImageFont.load_default()
        text = "Shutting Down..."
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (240 - (bbox[2] - bbox[0])) // 2
        y = (240 - (bbox[3] - bbox[1])) // 2
        draw.text((x, y), text, fill="white", font=font)
        device.display(loadingtxt)


def list_bin_indices():
    bin_dir = os.path.join(BASE_DIR, "bin")
    files = os.listdir(bin_dir)
    indices = []
    for f in files:
        if f.endswith(".bin"):
            name = os.path.splitext(f)[0]
            if name.isdigit():
                indices.append(int(name))
    return sorted(indices)

cache = {}  # index -> (frames, durations)

def load_bundled_bin(index):
    if index in cache:
        return cache[index]

    bin_path = os.path.join(BASE_DIR, "bin", f"{index}.bin")
    if not os.path.exists(bin_path):
        print(f"Missing file: {bin_path}")
        oled_print.print(f"Missing file: {bin_path}")
        return [], []

    with open(bin_path, "rb") as f:
        header = f.read(6)
        if len(header) < 6:
            print("Incomplete header.")
            oled_print.print("Incomplete header.")
            return [], []

        frame_count, width, height = struct.unpack("<HHH", header)
        duration_data = f.read(4 * frame_count)
        durations = list(struct.unpack(f"<{frame_count}f", duration_data))

        frame_size = width * height * 2
        frames = []

        for i in range(frame_count):
            raw = f.read(frame_size)
            if len(raw) < frame_size:
                print(f"Unexpected EOF while reading frame {i}")
                oled_print.print(f"Unexpected EOF while reading frame {i}")
                break
            frame = Image.frombytes("RGB", (width, height), raw, "raw", "BGR;16")
            frames.append(frame)

    cache[index] = (frames, durations)
    return frames, durations

oled_print = OLEDPrint(oled)
show_loading()

def preload_all_bins(indices):
    print("Preloading all .bin files into RAM...")
    oled_print.print("Preloading all .bin files into RAM...")
    for index in indices:
        if index not in cache:
            frames, durations = load_bundled_bin(index)
            if frames:
                print(f"Preloaded GIF #{index} with {len(frames)} frames.")
                oled_print.print(f"Preloaded GIF #{index} with {len(frames)} frames.")
            else:
                print(f"Failed to load GIF #{index}.")
                oled_print.print(f"Failed to load GIF #{index}.")
    print("Preloading complete.\n")
    oled_print.print("Preloading complete.\n")

indices = list_bin_indices()
if not indices:
    print("No .bin files found in /bin.")
    oled_print.print("No .bin files found in /bin.")
    sys.exit(1)

show_loading()
preload_all_bins(indices)

current_index_pos = 0
current_index = indices[current_index_pos]
frames, durations = cache.get(current_index, ([], []))

changeGIF_button = Button(24, bounce_time=0.2)  # Next GIF
exit_button = Button(23, bounce_time=0.2)    # Quit program

change_gif = False
should_quit = False

def changeGIF():
    global current_index_pos, current_index, change_gif
    current_index_pos = (current_index_pos + 1) % len(indices)
    current_index = indices[current_index_pos]
    print(f"Switching to GIF #{current_index}")
    oled_print.print(f"Switching to GIF #{current_index}")
    change_gif = True

def quit_program():
    global should_quit
    print("Exit button pressed.")
    oled_print.print("Exit button pressed.")
    show_shutdown()
    time.sleep(1)
    should_quit = True

changeGIF_button.when_pressed = changeGIF
exit_button.when_pressed = quit_program

try:
    while not should_quit:
        for frame, delay in zip(frames, durations):
            start = time.monotonic()
            device.display(frame)
            elapsed = time.monotonic() - start
            time.sleep(max(0, delay - elapsed))

            if change_gif:
                change_gif = False
                frames, durations = cache.get(current_index, ([], []))
                break

except KeyboardInterrupt:
    device.clear()
    print("Exiting via CTRL+C")
    show_shutdown()
    oled_print.print("Exiting via CTRL+C")
    time.sleep(1)
    sys.exit(0)
