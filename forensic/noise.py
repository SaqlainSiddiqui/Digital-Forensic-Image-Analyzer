from pathlib import Path

import cv2
import numpy as np


MAX_ANALYSIS_DIMENSION = 2000


def resize_for_analysis(image):
    """
    Resize large images while preserving their aspect ratio.
    """

    height, width = image.shape[:2]

    largest_dimension = max(width, height)

    if largest_dimension <= MAX_ANALYSIS_DIMENSION:
        return image

    scale = MAX_ANALYSIS_DIMENSION / largest_dimension

    new_width = int(width * scale)
    new_height = int(height * scale)

    return cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )


def calculate_noise_statistics(noise_image):
    """
    Calculate statistics from the normalized noise image.
    """

    noise_array = noise_image.astype(np.float32)

    mean_noise = float(np.mean(noise_array))
    standard_deviation = float(np.std(noise_array))
    maximum_noise = int(np.max(noise_array))

    return {
        "mean": round(mean_noise, 4),
        "standard_deviation": round(
            standard_deviation,
            4
        ),
        "maximum": maximum_noise,
    }


def analyze_noise(image_path, output_directory):
    """
    Generate a noise map using a high-frequency residual.

    Returns a dictionary containing the generated image path
    and noise statistics.
    """

    image_path = Path(image_path)
    output_directory = Path(output_directory)

    try:

        # -----------------------------------------
        # 1. Make sure output directory exists
        # -----------------------------------------

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )


        # -----------------------------------------
        # 2. Read the image
        # -----------------------------------------

        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_COLOR
        )

        if image is None:

            return {
                "success": False,
                "error": (
                    "OpenCV could not read the uploaded image."
                )
            }


        # -----------------------------------------
        # 3. Resize large images
        # -----------------------------------------

        image = resize_for_analysis(image)


        # -----------------------------------------
        # 4. Convert to grayscale
        # -----------------------------------------

        grayscale = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )


        # -----------------------------------------
        # 5. Create smooth image
        # -----------------------------------------

        blurred = cv2.GaussianBlur(
            grayscale,
            (5, 5),
            0
        )


        # -----------------------------------------
        # 6. Extract high-frequency residual
        # -----------------------------------------

        residual = cv2.absdiff(
            grayscale,
            blurred
        )


        # -----------------------------------------
        # 7. Normalize residual
        # -----------------------------------------

        normalized_noise = cv2.normalize(
            residual,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        )

        normalized_noise = normalized_noise.astype(
            np.uint8
        )


        # -----------------------------------------
        # 8. Calculate statistics
        # -----------------------------------------

        statistics = calculate_noise_statistics(
            normalized_noise
        )


        # -----------------------------------------
        # 9. Create visualization
        # -----------------------------------------

        noise_visualization = cv2.applyColorMap(
            normalized_noise,
            cv2.COLORMAP_JET
        )


        # -----------------------------------------
        # 10. Save visualization
        # -----------------------------------------

        output_filename = (
            f"{image_path.stem}_noise.jpg"
        )

        output_path = (
            output_directory /
            output_filename
        )

        save_success = cv2.imwrite(
            str(output_path),
            noise_visualization
        )


        if not save_success:

            return {
                "success": False,
                "error": (
                    "OpenCV generated the noise map but "
                    "could not save the output image."
                )
            }


        # -----------------------------------------
        # 11. Verify that file actually exists
        # -----------------------------------------

        if not output_path.exists():

            return {
                "success": False,
                "error": (
                    "Noise map was not found after saving."
                )
            }


        # -----------------------------------------
        # 12. Return successful result
        # -----------------------------------------

        return {
            "success": True,

            "filename": output_filename,

            "path": (
                f"/static/generated/"
                f"{output_filename}"
            ),

            "width": int(
                normalized_noise.shape[1]
            ),

            "height": int(
                normalized_noise.shape[0]
            ),

            "mean": statistics["mean"],

            "standard_deviation": (
                statistics["standard_deviation"]
            ),

            "maximum": statistics["maximum"],
        }


    except Exception as error:

        return {
            "success": False,
            "error": (
                f"{type(error).__name__}: {str(error)}"
            )
        }