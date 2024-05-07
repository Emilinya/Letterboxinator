import os
from fractions import Fraction

import pytest
import numpy as np
from PIL import Image, ImageOps

from blur import blur

# pylint: disable=redefined-outer-name,unused-argument


@pytest.fixture()
def image_filenames():
    return ["png_test.png", "exif_test.jpg"]


@pytest.fixture()
def cleanup(image_filenames):
    yield
    for filename in image_filenames:
        path, extension = os.path.splitext(filename)
        os.remove(f"{path}_16x9{extension}")


def get_image_box(width: int, height: int):
    ratio = 16 / 9

    if width / height > ratio:
        new_width = width
        new_height = int(width / ratio)
    else:
        new_width = int(height * ratio)
        new_height = height

    # calc image box
    half_width_change = int((new_width - width) / 2)
    half_height_change = int((new_height - height) / 2)

    return (
        half_width_change,
        half_height_change,
        width + half_width_change,
        height + half_height_change,
    )


def test_blur(image_filenames, cleanup):
    for filename in image_filenames:
        blur(filename)
        path, extension = os.path.splitext(filename)
        letterboxed_image = Image.open(f"{path}_16x9{extension}")

        width, height = letterboxed_image.size

        # is image 16x9?
        assert Fraction(width, height).limit_denominator(100) == Fraction(16, 9)

        # is center of blured image equal to the origional?
        image = Image.open(filename)
        ImageOps.exif_transpose(image, in_place=True)

        image_box = get_image_box(*image.size)
        cropped_letterbox = letterboxed_image.crop(image_box)

        image_array = np.array(image)
        letterbox_array = np.array(cropped_letterbox)

        # image arrays are u8, we must be carefull to avoid underflow
        difference = np.where(
            image_array > letterbox_array,
            image_array - letterbox_array,
            letterbox_array - image_array,
        )

        assert np.average(difference) < 1
