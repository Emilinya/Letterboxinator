import os

from PIL import Image, ImageFilter, ImageOps


def blur(filename: str, ratio: tuple[float, float] = (16, 9)):
    path, extension = os.path.splitext(filename)

    num_ratio = ratio[0] / ratio[1]
    image = Image.open(filename)

    # orient image correctly
    image = ImageOps.exif_transpose(image)

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

    # create blured sections
    black_image = Image.new("RGB", (width, height), color="black")

    blured_image = image.resize((new_width, new_height))
    blured_image.paste(black_image, img_box)
    blured_image = blured_image.filter(filter=ImageFilter.GaussianBlur(radius=70))

    # create letterbox
    letterboxed_image = image.resize((new_width, new_height))
    letterboxed_image.paste(blured_image, (0, 0, new_width, new_height))
    letterboxed_image.paste(image, img_box)

    letterboxed_image.save(
        f"{path}_{ratio[0]:.20g}x{ratio[1]:.20g}{extension}",
        quality=95,
        icc_profile=letterboxed_image.info.get("icc_profile", ""),
    )


if __name__ == "__main__":
    blur("exif_test.jpg")
    blur("png_test.png")
