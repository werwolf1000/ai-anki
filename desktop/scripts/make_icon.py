"""Генерирует assets/icon.png и icon.ico (градиентная карточка с буквой A)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets"
S = 1024


def gradient(size):
    img = Image.new("RGBA", (size, size))
    a, b = (139, 92, 246), (244, 63, 94)
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)
    return img


def main():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # задняя карточка
    back = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(back).rounded_rectangle((120, 190, 700, 900), radius=130, fill=(28, 28, 44, 255), outline=(139, 92, 246, 255), width=34)
    img.alpha_composite(back.rotate(8, resample=Image.BICUBIC, center=(410, 545)))
    # тень и передняя карточка
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((300, 110, 900, 860), radius=140, fill=255)
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shadow.putalpha(mask.filter(ImageFilter.GaussianBlur(30)).point(lambda v: v * 0.6))
    img.alpha_composite(shadow, (0, 30))
    front = gradient(S)
    front.putalpha(mask)
    img.alpha_composite(front)
    d = ImageDraw.Draw(img)
    d.line([(450, 700), (600, 300), (750, 700)], fill="white", width=74, joint="curve")
    d.line([(505, 560), (695, 560)], fill="white", width=66)
    for p in [(450, 700), (750, 700)]:
        d.ellipse((p[0] - 37, p[1] - 37, p[0] + 37, p[1] + 37), fill="white")
    OUT.mkdir(exist_ok=True)
    img.resize((512, 512), Image.LANCZOS).save(OUT / "icon.png")
    img.save(OUT / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("icon:", OUT)


if __name__ == "__main__":
    main()
