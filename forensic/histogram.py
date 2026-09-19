from pathlib import Path

import matplotlib

# IMPORTANT:
# Flask runs analysis inside request threads.
# Agg prevents Matplotlib from trying to use Tkinter.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import cv2


MAX_ANALYSIS_DIMENSION = 2000


def resize_for_analysis(image):
    """
    Resize large images while preserving aspect ratio.
    """

    height, width = image.shape[:2]

    largest_dimension = max(width, height)

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


def generate_histogram(image_path, output_directory):
    """
    Generate RGB and grayscale histogram images.

    Uses Matplotlib's non-GUI Agg backend so that
    histogram generation works correctly inside Flask.
    """

    image_path = Path(image_path)
    output_directory = Path(output_directory)

    try:

        # -----------------------------------------
        # Create output directory
        # -----------------------------------------

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )


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
                    "OpenCV could not read the image."
                )
            }


        # -----------------------------------------
        # Resize large image
        # -----------------------------------------

        image = resize_for_analysis(image)


        # -----------------------------------------
        # Split channels
        # -----------------------------------------

        blue, green, red = cv2.split(image)

        grayscale = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )


        # =========================================
        # RGB HISTOGRAM
        # =========================================

        rgb_filename = (
            f"{image_path.stem}_rgb_histogram.png"
        )

        rgb_output = (
            output_directory /
            rgb_filename
        )


        figure = plt.figure(
            figsize=(10, 5)
        )

        try:

            plt.hist(
                red.ravel(),
                bins=256,
                range=(0, 256),
                alpha=0.5,
                label="Red"
            )

            plt.hist(
                green.ravel(),
                bins=256,
                range=(0, 256),
                alpha=0.5,
                label="Green"
            )

            plt.hist(
                blue.ravel(),
                bins=256,
                range=(0, 256),
                alpha=0.5,
                label="Blue"
            )

            plt.title("RGB Histogram")
            plt.xlabel("Pixel Intensity")
            plt.ylabel("Frequency")
            plt.xlim(0, 255)
            plt.legend()
            plt.tight_layout()

            figure.savefig(
                rgb_output,
                dpi=120,
                format="png"
            )

        finally:

            plt.close(figure)


        # =========================================
        # GRAYSCALE HISTOGRAM
        # =========================================

        grayscale_filename = (
            f"{image_path.stem}_grayscale_histogram.png"
        )

        grayscale_output = (
            output_directory /
            grayscale_filename
        )


        figure = plt.figure(
            figsize=(10, 5)
        )

        try:

            plt.hist(
                grayscale.ravel(),
                bins=256,
                range=(0, 256)
            )

            plt.title("Grayscale Histogram")
            plt.xlabel("Pixel Intensity")
            plt.ylabel("Frequency")
            plt.xlim(0, 255)
            plt.tight_layout()

            figure.savefig(
                grayscale_output,
                dpi=120,
                format="png"
            )

        finally:

            plt.close(figure)


        # =========================================
        # VERIFY OUTPUT
        # =========================================

        if not rgb_output.exists():

            return {
                "success": False,
                "error": (
                    "RGB histogram file was not created."
                )
            }


        if not grayscale_output.exists():

            return {
                "success": False,
                "error": (
                    "Grayscale histogram file "
                    "was not created."
                )
            }


        # =========================================
        # SUCCESS
        # =========================================

        return {

            "success": True,

            "rgb_path": (
                f"/static/generated/"
                f"{rgb_filename}"
            ),

            "grayscale_path": (
                f"/static/generated/"
                f"{grayscale_filename}"
            ),

            "rgb_filename": rgb_filename,

            "grayscale_filename": (
                grayscale_filename
            ),
        }


    except Exception as error:

        plt.close("all")

        return {
            "success": False,
            "error": (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )
        }