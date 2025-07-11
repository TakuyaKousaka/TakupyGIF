# Takuya's pyGIF script

This Python script plays preprocessed animations that's converted from GIFs, uses 2 displays.
- **ST7789** 240x240 IPS (via SPI) (GIF Player)
- **SSD1306** 128x64 OLED (via I2C) (Status display)

It supports loading images, fallback text rendering, graceful shutdown, and button-triggered GIF switching using GPIO input.

## Functions

- Dual display for max eyecandy
- Preprocessed bin file format for fast(ish) GIF playback
- GPIO button input to cycle GIFs and exit the program
- Caching for reduced I/O during playback

## Hardware Needed

- Raspberry Pi 3+ (Developed and Tested on a Raspberry Pi Zero 2W)
- ST7789 240x240 SPI IPS display
- SSD1306 128x64 I2C OLED display
- 2 GPIO-connected buttons:
  - GPIO 24: Next GIF
  - GPIO 23: Quit program

## Dependencies

Install via `pip` within the venv (assuming venv is on a parent folder):

```bash
../luma-env/bin/python -m pip install pillow gpiozero rpi-lgpio luma.oled luma.lcd
```


## Folder Structure

```
project/
├── gif/                 -/Folder containing 240x240 resolution gifs (Exact resolution match isn't required, make sure it's 1:1 aspect ratio)
├── bin/                 -/Folder containing numbered preprocessed .bin animation files (e.g. 0.bin, 1.bin...)
├── loading.png          -/Optional splash image for ST7789
├── loading_oled.png     -/Optional splash image for SSD1306
├── lcdgif.py            -/Main player script
└── preprocess_gif.py    -/GIF to Custom .bin pre-processor
```

## Usage

0. Setup a Python venv for luma-lcd
1. Create `gif` and `bin` folder in the same directory as the python scripts

- **Input folder:** `gif/`  
  - Expecting: numbered GIFs (e.g., `0.gif`, `1.gif`, `2.gif`, ...)
- **Output folder:** `bin/`  
  - Output files: `0.bin`, `1.bin`, etc.

1. Place GIFs in the `gif/` directory. They must be named numerically (e.g. `0.gif`, `1.gif`, `2.gif`...).
2. Run the the pre processor ```python preprocess_gif.py```
2. Run the viewer (assuming venv is on a parent folder):

```bash
../luma-env/bin/python lcdgif.py
```

3. Use the connected GPIO buttons:
   - **GPIO 24**: Switch to next GIF
   - **GPIO 23**: Exit and shutdown cleanly


## Custom GIF Binary File Format

Each `.gif` is:
- Resized to **240x240**
- Converted from RGB888 to RGB565 format
- Encoded with a header:
  - `frame_count` (2 bytes)
  - `width` (2 bytes)
  - `height` (2 bytes)
- Followed by:
  - 4-byte float durations for each frame
  - Raw RGB565 frame data (per frame)

Each `.bin` animation is structured as:
- 6-byte header: `<frame_count:2><width:2><height:2>`
- 4-byte float durations for each frame
- Raw RGB565 frame data per frame

Frames are decoded using Pillow from raw bytes and played with precise frame delay timing.



## Splash and Fallback

- If `loading.png` or `loading_oled.png` is missing, fallback text will be shown instead.



## Clean Exit

- Pressing the exit button or `CTRL+C` displays a "Shutting Down..." message on the ST7789 and OLED before quitting.

## Credits
- Uses the [Luma Display Libraries](https://github.com/rm-hull/luma.core)
- [Pillow](https://github.com/python-pillow/Pillow) for image manipulation