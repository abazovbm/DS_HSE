# logging here
"""
Утилита конвертации изображений. CLI-интерфейс.
"""
import argparse
from pathlib import Path
from PIL import Image
import sys


def convert_image(input_path: Path, output_format: str, quality: int = 90) -> Path:
    """Конвертирует изображение в указанный формат."""
    img = Image.open(input_path)
    if output_format.upper() in ("JPG", "JPEG") and img.mode == "RGBA":
        img = img.convert("RGB")
    output_path = input_path.with_suffix("." + output_format.lower())
    save_kwargs = {}
    if output_format.upper() in ("JPG", "JPEG"):
        save_kwargs["quality"] = quality
    img.save(output_path, **save_kwargs)
    return output_path


def resize_image(input_path: Path, max_size: int) -> Path:
    img = Image.open(input_path)
    img.thumbnail((max_size, max_size))
    output_path = input_path.parent / f"{input_path.stem}_resized{input_path.suffix}"
    img.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Конвертер изображений")
    parser.add_argument("input", type=Path, help="Путь к изображению")
    parser.add_argument("--format", default="png", help="Целевой формат")
    parser.add_argument("--quality", type=int, default=90, help="Качество для JPEG")
    parser.add_argument("--resize", type=int, help="Уменьшить до N пикселей")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Файл {args.input} не найден", file=sys.stderr)
        sys.exit(1)

    if args.resize:
        result = resize_image(args.input, args.resize)
    else:
        result = convert_image(args.input, args.format, args.quality)
    print(f"Готово: {result}")


if __name__ == "__main__":
    main()
