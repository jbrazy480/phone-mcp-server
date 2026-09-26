"""Render actual offline demo output as a terminal GIF using only Pillow."""

import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    run = subprocess.run([sys.executable, '-m', 'phone_mcp.demo'], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    lines = []
    for line in run.stdout.splitlines():
        lines.extend(textwrap.wrap(line, width=95) or [''])
    font = ImageFont.load_default(size=17)
    frames = []
    for end in range(2, len(lines)+3, 2):
        frame = Image.new('RGB', (1080, 590), '#202d3d')
        draw = ImageDraw.Draw(frame)
        draw.rounded_rectangle((18, 18, 1062, 572), radius=14, fill='#263348', outline='#344861')
        draw.text((40, 32), 'phone-mcp-server  |  offline demo  |  no keys', font=font, fill='#9dc8ff')
        draw.line((36, 65, 1044, 65), fill='#344861', width=2)
        visible = lines[:end][-19:]
        for i, line in enumerate(visible):
            color = '#f1ca78' if 'GUARD' in line else '#80dfb3' if 'RESULT' in line else '#e3ecf7'
            draw.text((40, 82+i*24), line, font=font, fill=color)
        frames.append(frame)
    output = ROOT/'docs/demo.gif'
    output.parent.mkdir(exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=[850]*(len(frames)-1)+[2500], loop=0, optimize=True)
    assert output.stat().st_size < 2_000_000
    print(f'Rendered {output.relative_to(ROOT)}: {output.stat().st_size} bytes')


if __name__ == '__main__':
    main()
