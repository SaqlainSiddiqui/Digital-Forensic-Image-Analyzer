from pathlib import Path

import cv2
import numpy as np


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


def normalize_map(data):
    """
    Normalize an array to the range 0-255.
    """

    data = data.astype(np.float32)

    minimum = np.min(data)
    maximum = np.max(data)

    if maximum - minimum < 1e-8:
        return np.zeros_like(
            data,
            dtype=np.uint8
        )

    normalized = (
        (data - minimum) /
        (maximum - minimum)
    ) * 255.0

    return normalized.astype(np.uint8)


def calculate_local_variation(grayscale):
    """
    Calculate local pixel variation using local mean
    and local squared mean.
    """

    grayscale_float = grayscale.astype(
        np.float32
    )

    local_mean = cv2.GaussianBlur(
        grayscale_float,
        (0, 0),
        sigmaX=5
    )

    local_squared_mean = cv2.GaussianBlur(
        grayscale_float ** 2,
        (0, 0),
        sigmaX=5
    )

    variance = (
        local_squared_mean -
        local_mean ** 2
    )

    variance = np.maximum(
        variance,
        0
    )

    local_std = np.sqrt(variance)

    return local_std


def create_high_frequency_map(grayscale):
    """
    Extract high-frequency image variation.
    """

    blurred = cv2.GaussianBlur(
        grayscale,
        (5, 5),
        0
    )

    residual = cv2.absdiff(
        grayscale,
        blurred
    )

    return residual


def create_edge_map(grayscale):
    """
    Calculate edge strength using Sobel gradients.
    """

    grayscale_float = grayscale.astype(
        np.float32
    )

    gradient_x = cv2.Sobel(
        grayscale_float,
        cv2.CV_32F,
        1,
        0,
        ksize=3
    )

    gradient_y = cv2.Sobel(
        grayscale_float,
        cv2.CV_32F,
        0,
        1,
        ksize=3
    )

    edge_strength = cv2.magnitude(
        gradient_x,
        gradient_y
    )

    return edge_strength


def create_combined_anomaly_map(grayscale):
    """
    Combine high-frequency variation, local variation
    and edge response into a single anomaly indicator.

    This is a heuristic visualization and not a classifier.
    """

    high_frequency = (
        create_high_frequency_map(
            grayscale
        )
    )

    local_variation = (
        calculate_local_variation(
            grayscale
        )
    )

    edge_strength = (
        create_edge_map(
            grayscale
        )
    )

    # Normalize each signal independently.
    high_frequency_normalized = (
        normalize_map(high_frequency)
        .astype(np.float32)
        / 255.0
    )

    local_variation_normalized = (
        normalize_map(local_variation)
        .astype(np.float32)
        / 255.0
    )

    edge_normalized = (
        normalize_map(edge_strength)
        .astype(np.float32)
        / 255.0
    )

    # Weighted combination.
    #
    # High-frequency residual receives the largest weight.
    # Local variation contributes next.
    # Edges receive a smaller weight because natural edges
    # can produce strong responses.
    combined = (
        0.50 * high_frequency_normalized
        +
        0.35 * local_variation_normalized
        +
        0.15 * edge_normalized
    )

    return normalize_map(combined)


def detect_regions(anomaly_map):
    """
    Detect high-response regions from the anomaly map.

    A percentile threshold is used so that the method adapts
    to different images.
    """

    threshold_value = float(
        np.percentile(
            anomaly_map,
            97
        )
    )

    binary = np.where(
        anomaly_map >= threshold_value,
        255,
        0
    ).astype(np.uint8)

    # Remove tiny isolated pixels.
    kernel = np.ones(
        (5, 5),
        np.uint8
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel
    )

    # Join nearby response areas.
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    height, width = anomaly_map.shape

    image_area = height * width

    minimum_region_area = max(
        150,
        int(image_area * 0.00005)
    )

    regions = []

    for contour in contours:

        area = cv2.contourArea(
            contour
        )

        if area < minimum_region_area:
            continue

        x, y, w, h = cv2.boundingRect(
            contour
        )

        region = {
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "area": int(area),
            "area_percentage": round(
                (area / image_area) * 100,
                4
            ),
        }

        regions.append(region)

    # Largest regions first.
    regions.sort(
        key=lambda region: region["area"],
        reverse=True
    )

    return regions, threshold_value, binary


def create_heatmap(anomaly_map):
    """
    Convert anomaly intensity into a color heatmap.
    """

    return cv2.applyColorMap(
        anomaly_map,
        cv2.COLORMAP_JET
    )


def create_overlay(
    original,
    heatmap,
    regions
):
    """
    Create an overlay showing the anomaly heatmap
    and detected region boundaries.
    """

    heatmap_overlay = cv2.addWeighted(
        original,
        0.60,
        heatmap,
        0.40,
        0
    )

    for index, region in enumerate(
        regions,
        start=1
    ):

        x = region["x"]
        y = region["y"]
        w = region["width"]
        h = region["height"]

        cv2.rectangle(
            heatmap_overlay,
            (x, y),
            (x + w, y + h),
            (0, 0, 255),
            2
        )

        cv2.putText(
            heatmap_overlay,
            f"Region {index}",
            (x, max(y - 8, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )

    return heatmap_overlay


def calculate_region_indicator(
    anomaly_map,
    regions
):
    """
    Calculate a simple normalized indicator based on the
    detected high-response regions.

    This is not a probability of manipulation.
    """

    mean_anomaly = float(
        np.mean(anomaly_map)
    )

    if not regions:
        region_coverage = 0.0
    else:
        region_coverage = sum(
            region["area_percentage"]
            for region in regions
        )

    # Cap coverage contribution.
    coverage_component = min(
        region_coverage / 10.0,
        1.0
    )

    # Normalize mean anomaly.
    mean_component = min(
        mean_anomaly / 255.0,
        1.0
    )

    indicator = (
        0.65 * mean_component
        +
        0.35 * coverage_component
    )

    return round(
        indicator * 100,
        2
    )


def detect_suspicious_regions(
    image_path,
    output_directory
):
    """
    Generate a heuristic potential-inconsistency heatmap
    and region overlay.
    """

    image_path = Path(image_path)
    output_directory = Path(
        output_directory
    )

    try:

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
                    "OpenCV could not read "
                    "the image."
                )
            }


        # -----------------------------------------
        # Resize
        # -----------------------------------------

        image = resize_for_analysis(
            image
        )


        # -----------------------------------------
        # Grayscale
        # -----------------------------------------

        grayscale = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )


        # -----------------------------------------
        # Combined anomaly map
        # -----------------------------------------

        anomaly_map = (
            create_combined_anomaly_map(
                grayscale
            )
        )


        # -----------------------------------------
        # Detect regions
        # -----------------------------------------

        regions, threshold_value, binary = (
            detect_regions(
                anomaly_map
            )
        )


        # Limit displayed regions.
        # This prevents the UI from becoming overloaded.
        regions = regions[:10]


        # -----------------------------------------
        # Heatmap
        # -----------------------------------------

        heatmap = create_heatmap(
            anomaly_map
        )


        # -----------------------------------------
        # Overlay
        # -----------------------------------------

        overlay = create_overlay(
            image,
            heatmap,
            regions
        )


        # -----------------------------------------
        # Output filenames
        # -----------------------------------------

        heatmap_filename = (
            f"{image_path.stem}"
            f"_suspicious_heatmap.jpg"
        )

        overlay_filename = (
            f"{image_path.stem}"
            f"_suspicious_regions.jpg"
        )

        mask_filename = (
            f"{image_path.stem}"
            f"_suspicious_mask.jpg"
        )


        heatmap_path = (
            output_directory /
            heatmap_filename
        )

        overlay_path = (
            output_directory /
            overlay_filename
        )

        mask_path = (
            output_directory /
            mask_filename
        )


        # -----------------------------------------
        # Save files
        # -----------------------------------------

        heatmap_saved = cv2.imwrite(
            str(heatmap_path),
            heatmap
        )

        overlay_saved = cv2.imwrite(
            str(overlay_path),
            overlay
        )

        mask_saved = cv2.imwrite(
            str(mask_path),
            binary
        )


        if not (
            heatmap_saved
            and overlay_saved
            and mask_saved
        ):

            return {
                "success": False,
                "error": (
                    "One or more suspicious-region "
                    "output images could not be saved."
                )
            }


        # -----------------------------------------
        # Calculate indicator
        # -----------------------------------------

        indicator = (
            calculate_region_indicator(
                anomaly_map,
                regions
            )
        )


        # -----------------------------------------
        # Return results
        # -----------------------------------------

        return {

            "success": True,

            "heatmap_path": (
                f"/static/generated/"
                f"{heatmap_filename}"
            ),

            "overlay_path": (
                f"/static/generated/"
                f"{overlay_filename}"
            ),

            "mask_path": (
                f"/static/generated/"
                f"{mask_filename}"
            ),

            "width": int(
                anomaly_map.shape[1]
            ),

            "height": int(
                anomaly_map.shape[0]
            ),

            "region_count": len(
                regions
            ),

            "regions": regions,

            "threshold": round(
                threshold_value,
                2
            ),

            "indicator": indicator,

        }


    except Exception as error:

        return {
            "success": False,
            "error": (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )
        }