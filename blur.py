from PIL import Image, ImageFilter


def blur(filename, ratio=(16, 9)):
    *body, extension = filename.split(".")
    path = ".".join(body)

    num_ratio = ratio[0] / ratio[1]

    image = Image.open(filename)
    width, height = image.size

    if width/height > num_ratio:
        new_width = width
        new_height = int(width / num_ratio)
    else:
        new_width = int(height * num_ratio)
        new_height = height

    # calc image box
    half_width_change = int((new_width - width)/2)
    half_height_change = int((new_height - height)/2)

    print(half_width_change, half_height_change)
    if half_width_change == half_height_change == 0:
        raise ValueError(f"Image is already {ratio[0]:.20g}x{ratio[1]:.20g}")

    img_box = (
        half_width_change, half_height_change,
        width + half_width_change, height + half_height_change
    )

    # create blured sections
    black_image = Image.new('RGB', (width, height), color="black")

    blured_image = image.resize((new_width, new_height))
    blured_image.paste(black_image, img_box)
    blured_image = blured_image.filter(
        filter=ImageFilter.GaussianBlur(radius=70))

    # create letterbox
    letterboxed_image = Image.new(
        'RGB', (new_width, new_height), color="black")
    letterboxed_image.paste(blured_image, (0, 0, new_width, new_height))
    letterboxed_image.paste(image, img_box)

    letterboxed_image.save(path+f"_{ratio[0]:.20g}x{ratio[1]:.20g}."+extension)
