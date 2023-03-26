"""Resize the scene images."""

import argparse
import os
import pathlib
import sys

import PIL
import PIL.Image


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    this_path = pathlib.Path(os.path.realpath(__file__))

    images_dir = this_path.parent.parent / "dancerunaway/media/images"

    for level_dir in sorted(
        pth_dir
        for pth_dir in images_dir.glob("level*")
        if pth_dir.is_dir()
    ):
        for pth in sorted(level_dir.glob("*.png")):
            with PIL.Image.open(str(pth)) as image:
                png_info = dict()
                if image.mode not in ['RGB', 'RGBA']:
                    image = image.convert('RGBA')
                    png_info = image.info

                resized = image.resize((640, 480))

            resized.save(str(pth), **png_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())
