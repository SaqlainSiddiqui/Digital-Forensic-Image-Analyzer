from pathlib import Path

import cv2
import numpy as np


MAX_ANALYSIS_DIMENSION = 2000


def resize_for_analysis(image):
    """
    Resize large images while preserving aspect ratio.
    """

    height, width = image.shape[:2]

    largest_dimension = max(
        width,
        height
    )

    if largest_dimension <= MAX_ANALYSIS_DIMENSION:
        return image

    scale = (
        MAX_ANALYSIS_DIMENSION /
        largest_dimension
    )

    new_width = int(width * scale)
    new_height = int(height * scale)

    return cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )


def calculate_entropy(grayscale):
    """
    Calculate Shannon entropy from grayscale pixels.
    """

    histogram = cv2.calcHist(
        [grayscale],
        [0],
        None,
        [256],
        [0, 256]
    )

    histogram = histogram.flatten()

    total_pixels = np.sum(histogram)

    if total_pixels == 0:
        return 0.0

    probabilities = (
        histogram /
        total_pixels
    )

    probabilities = probabilities[
        probabilities > 0
    ]

    entropy = -np.sum(
        probabilities *
        np.log2(probabilities)
    )

    return float(entropy)


def calculate_statistics(image_path):
    """
    Calculate quantitative image statistics.
    """

    image_path = Path(image_path)

    try:

        # -----------------------------------------
        # Read image
        # -----------------------------------------

        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_COLOR
        )

        if image is None:

            return {
                "success": False,
                "error": (
                    "OpenCV could not read "
                    "the image."
                )
            }


        # -----------------------------------------
        # Resize for analysis
        # -----------------------------------------

        image = resize_for_analysis(image)


        # -----------------------------------------
        # Convert to grayscale
        # -----------------------------------------

        grayscale = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )


        # -----------------------------------------
        # Calculate statistics
        # -----------------------------------------

        mean_intensity = float(
            np.mean(grayscale)
        )

        standard_deviation = float(
            np.std(grayscale)
        )

        minimum_intensity = int(
            np.min(grayscale)
        )

        maximum_intensity = int(
            np.max(grayscale)
        )

        entropy = calculate_entropy(
            grayscale
        )


        # -----------------------------------------
        # Image dimensions
        # -----------------------------------------

        height, width = grayscale.shape


        # -----------------------------------------
        # Return result
        # -----------------------------------------

        return {

            "success": True,

            "width": int(width),

            "height": int(height),

            "brightness": round(
                mean_intensity,
                4
            ),

            "contrast": round(
                standard_deviation,
                4
            ),

            "mean_intensity": round(
                mean_intensity,
                4
            ),

            "standard_deviation": round(
                standard_deviation,
                4
            ),

            "minimum_intensity": (
                minimum_intensity
            ),

            "maximum_intensity": (
                maximum_intensity
            ),

            "entropy": round(
                entropy,
                4
            ),
        }


    except Exception as error:

        return {
            "success": False,
            "error": (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )
        }