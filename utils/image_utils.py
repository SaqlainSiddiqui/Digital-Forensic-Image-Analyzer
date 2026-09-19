def allowed_image_extension(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in {"jpg", "jpeg", "png", "bmp", "webp"}
    )