from PIL import Image, ImageSequence
import os
import re
import struct

GIF_FOLDER = "gif"
OUTPUT_FOLDER = "bin"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def list_gif_files():
    files = os.listdir(GIF_FOLDER)
    gifs = sorted([f for f in files if re.match(r"\d+\.gif$", f)], key=lambda x: int(x.split(".")[0]))
    return gifs

def rgb888_to_rgb565(data):
    result = bytearray()
    for i in range(0, len(data), 3):
        r = data[i] >> 3
        g = data[i+1] >> 2
        b = data[i+2] >> 3
        rgb565 = (r << 11) | (g << 5) | b
        result += struct.pack('<H', rgb565)
    return result

def preprocess_gif_to_bin(filename):
    input_path = os.path.join(GIF_FOLDER, filename)
    index = os.path.splitext(filename)[0]
    output_path = os.path.join(OUTPUT_FOLDER, f"{index}.bin")

    print(f"Processing {filename} → {output_path}")

    img = Image.open(input_path)
    frames = []
    durations = []

    for frame in ImageSequence.Iterator(img):
        frame_rgb = frame.convert("RGB").resize((240, 240))
        raw_bytes = frame_rgb.tobytes()
        rgb565_frame = rgb888_to_rgb565(raw_bytes)
        frames.append(rgb565_frame)
        delay = max(frame.info.get("duration", 100) / 1000, 0.05)  # in seconds
        durations.append(delay)

    frame_count = len(frames)
    width, height = 240, 240

    with open(output_path, "wb") as f:
        f.write(struct.pack("<HHH", frame_count, width, height))
        f.write(struct.pack(f"<{frame_count}f", *durations))
        for raw_frame in frames:
            f.write(raw_frame)

def main():
    gif_files = list_gif_files()
    if not gif_files:
        print(f"No numbered .gif files found in {GIF_FOLDER}/")
        return

    for gif_file in gif_files:
        preprocess_gif_to_bin(gif_file)

if __name__ == "__main__":
    main()
