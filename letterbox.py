import os

import numpy as np
from PIL import Image, ImageFilter, ImageOps


def apply_blur(
    image: Image.Image,
    new_size: tuple[int, int],
    img_box: tuple[int, int, int, int],
    radius: int,
):
    width, height = image.size
    new_width, new_height = new_size

    # create blured sections
    black_image = Image.new(image.mode, (width, height), color="black")

    blured_image = image.resize((new_width, new_height))
    blured_image.paste(black_image, img_box)
    blured_image = blured_image.filter(filter=ImageFilter.GaussianBlur(radius=radius))

    # create letterbox
    letterboxed_image = image.resize((new_width, new_height))
    letterboxed_image.paste(blured_image, (0, 0, new_width, new_height))
    letterboxed_image.paste(image, img_box)

    return letterboxed_image


def apply_color(
    image: Image.Image,
    new_size: tuple[int, int],
    img_box: tuple[int, int, int, int],
    color: tuple[int, int, int, int],
):
    new_width, new_height = new_size

    letterboxed_image = Image.new(image.mode, (new_width, new_height), color=color)
    letterboxed_image.paste(image, img_box)

    return letterboxed_image


def apply_extrude(
    image: Image.Image,
    new_size: tuple[int, int],
    img_box: tuple[int, int, int, int],
):
    width, height = image.size
    new_width, new_height = new_size

    letterboxed_image = Image.new(image.mode, (new_width, new_height), color="black")
    letterboxed_image.paste(image, img_box)
    array = np.array(letterboxed_image)

    if img_box[0] != 0:
        array[:, : img_box[0]] = array[:, img_box[0]].reshape(height, 1, -1)
        array[:, img_box[2] :] = array[:, img_box[2] - 1].reshape(height, 1, -1)
    else:
        array[: img_box[1], :] = array[img_box[1], :].reshape(1, width, -1)
        array[img_box[3] :, :] = array[img_box[3] - 1, :].reshape(1, width, -1)

    return Image.fromarray(array)


def add_letterbox(
    filename: str,
    ratio: tuple[float, float] = (16, 9),
    mode="Blur",
    blur_radius=70,
    background_color: tuple[int, int, int, int] = (1, 1, 1, 1),
):
    path, extension = os.path.splitext(filename)

    num_ratio = ratio[0] / ratio[1]
    image = Image.open(filename)

    # P mode does not work, what other modes don't work?
    if image.mode == "P":
        image = image.convert("RGB")

    # orient image correctly
    ImageOps.exif_transpose(image, in_place=True)

    width, height = image.size
    if width / height > num_ratio:
        new_width = width
        new_height = int(width / num_ratio)
    else:
        new_width = int(height * num_ratio)
        new_height = height

    # calc image box
    half_width_change = int((new_width - width) / 2)
    half_height_change = int((new_height - height) / 2)

    if half_width_change == half_height_change == 0:
        raise ValueError(f"Image is already {ratio[0]:.20g}x{ratio[1]:.20g}")

    img_box = (
        half_width_change,
        half_height_change,
        width + half_width_change,
        height + half_height_change,
    )

    # create letterbox
    if mode == "Blur":
        letterboxed_image = apply_blur(
            image, (new_width, new_height), img_box, blur_radius
        )
    elif mode == "Color":
        letterboxed_image = apply_color(
            image, (new_width, new_height), img_box, background_color
        )
    elif mode == "Extrude":
        letterboxed_image = apply_extrude(image, (new_width, new_height), img_box)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    letterboxed_image.save(
        f"{path}_{ratio[0]:.20g}x{ratio[1]:.20g}{extension}",
        quality=95,
        icc_profile=letterboxed_image.info.get("icc_profile", ""),
    )
