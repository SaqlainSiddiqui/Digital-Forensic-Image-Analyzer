from pathlib import Path
from io import BytesIO

import numpy as np

from PIL import Image, ImageChops, ImageEnhance


MAX_ANALYSIS_DIMENSION = 2000
ELA_JPEG_QUALITY = 90


def resize_for_analysis(image):
    """
    Resize large images while preserving aspect ratio.
    """

    width, height = image.size

    largest_dimension = max(
        width,
        height
    )

    if largest_dimension <= MAX_ANALYSIS_DIMENSION:
        return image.copy()

    scale = (
        MAX_ANALYSIS_DIMENSION /
        largest_dimension
    )

    new_width = int(width * scale)
    new_height = int(height * scale)

    return image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )


def perform_ela(image_path, output_directory):
    """
    Perform Error Level Analysis.
    """

    image_path = Path(image_path)
    output_directory = Path(output_directory)

    try:

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        # -----------------------------------------
        # Open original image
        # -----------------------------------------

        with Image.open(image_path) as original:

            original = original.convert("RGB")

            analysis_image = resize_for_analysis(
                original
            )


        # -----------------------------------------
        # Recompress image
        # -----------------------------------------

        compressed_buffer = BytesIO()

        analysis_image.save(
            compressed_buffer,
            format="JPEG",
            quality=ELA_JPEG_QUALITY
        )

        compressed_buffer.seek(0)


        # -----------------------------------------
        # Open recompressed image
        # -----------------------------------------

        with Image.open(
            compressed_buffer
        ) as compressed:

            compressed = compressed.convert("RGB")

            difference = ImageChops.difference(
                analysis_image,
                compressed
            )


        # -----------------------------------------
        # Difference statistics
        # -----------------------------------------

        difference_array = np.asarray(
            difference,
            dtype=np.float32
        )

        maximum_difference = int(
            np.max(difference_array)
        )

        average_difference = float(
            np.mean(difference_array)
        )


        # -----------------------------------------
        # Amplify differences
        # -----------------------------------------

        scale = (
            255 / maximum_difference
            if maximum_difference > 0
            else 1
        )

        ela_image = ImageEnhance.Brightness(
            difference
        ).enhance(scale)


        # -----------------------------------------
        # Save ELA image
        # -----------------------------------------

        output_filename = (
            f"{image_path.stem}_ela.jpg"
        )

        output_path = (
            output_directory /
            output_filename
        )

        ela_image.save(
            output_path,
            format="JPEG",
            quality=95
        )


        if not output_path.exists():

            return {
                "success": False,
                "error": (
                    "ELA image was not found after saving."
                )
            }


        # -----------------------------------------
        # Return result
        # -----------------------------------------

        return {
            "success": True,

            "filename": output_filename,

            "path": (
                f"/static/generated/"
                f"{output_filename}"
            ),

            "width": difference.width,

            "height": difference.height,

            "maximum_difference": (
                maximum_difference
            ),

            "average_difference": round(
                average_difference,
                4
            ),

            "jpeg_quality": ELA_JPEG_QUALITY,
        }


    except Exception as error:

        return {
            "success": False,
            "error": (
                f"{type(error).__name__}: {str(error)}"
            )
        }