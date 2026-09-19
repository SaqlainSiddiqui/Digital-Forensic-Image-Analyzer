"""
Transparent heuristic scoring for the Digital Image Forensic Analyzer.

IMPORTANT:
This module does NOT determine whether an image is fake or authentic.

It produces an indicator score based on measurable signals from
the other forensic modules.
"""


EDITING_SOFTWARE_KEYWORDS = [
    "adobe photoshop",
    "photoshop",
    "adobe lightroom",
    "lightroom",
    "gimp",
    "paint.net",
    "affinity photo",
    "snapseed",
    "picsart",
    "pixlr",
    "canva",
]


def clamp(value, minimum=0, maximum=100):
    """Keep a numeric value inside a specified range."""

    return max(
        minimum,
        min(maximum, value)
    )


def calculate_metadata_indicator(metadata):
    """
    Calculate the metadata component.

    The presence of known editing software is treated as an
    indicator, not proof of manipulation.

    Missing EXIF metadata is NOT treated as suspicious.
    """

    if not metadata:
        return {
            "score": 0,
            "maximum": 15,
            "status": "No metadata result available.",
            "details": [],
        }

    fields = metadata.get(
        "fields",
        {}
    )

    details = []

    software_value = ""

    for key, value in fields.items():

        if key.lower() in {
            "software",
            "processingsoftware",
            "creatorsoftware",
        }:

            software_value = str(value).lower()

            break

    if not software_value:

        return {
            "score": 0,
            "maximum": 15,
            "status": "No editing software identified.",
            "details": [
                "No known editing software was found in EXIF."
            ],
        }

    detected_software = []

    for keyword in EDITING_SOFTWARE_KEYWORDS:

        if keyword in software_value:

            detected_software.append(
                keyword
            )

    if detected_software:

        details.append(
            "Editing-related software metadata was detected: "
            + ", ".join(detected_software)
        )

        details.append(
            "Software metadata can indicate that an image "
            "has passed through an editing application, but "
            "does not establish that the image was manipulated."
        )

        return {
            "score": 15,
            "maximum": 15,
            "status": "Editing software metadata detected.",
            "details": details,
        }

    return {
        "score": 0,
        "maximum": 15,
        "status": "Software metadata present but not identified as editing software.",
        "details": [
            f"Software metadata: {software_value}"
        ],
    }


def calculate_ela_indicator(ela):
    """
    Convert ELA average difference into a transparent
    heuristic indicator.

    These thresholds are intentionally simple reference
    thresholds rather than a trained forensic classifier.
    """

    if not ela or not ela.get("success"):

        return {
            "score": 0,
            "maximum": 30,
            "status": "ELA unavailable.",
            "details": [],
        }

    average_difference = float(
        ela.get(
            "average_difference",
            0
        )
    )

    maximum_difference = float(
        ela.get(
            "maximum_difference",
            0
        )
    )

    # Reference scale.
    if average_difference < 2:

        score = 5
        status = "Low ELA response."

    elif average_difference < 5:

        score = 12
        status = "Moderate ELA response."

    elif average_difference < 10:

        score = 20
        status = "Elevated ELA response."

    else:

        score = 28
        status = "High ELA response."

    # A maximum difference of zero is unusual for a JPEG
    # recompression comparison, so add a small adjustment
    # only when a measurable maximum exists.
    if maximum_difference > 0:

        score += 2

    score = clamp(
        score,
        0,
        30
    )

    return {
        "score": score,
        "maximum": 30,
        "status": status,
        "details": [
            f"Average ELA difference: {average_difference}",
            f"Maximum ELA difference: {maximum_difference}",
        ],
    }


def calculate_noise_indicator(noise):
    """
    Convert noise standard deviation into a heuristic indicator.
    """

    if not noise or not noise.get("success"):

        return {
            "score": 0,
            "maximum": 20,
            "status": "Noise analysis unavailable.",
            "details": [],
        }

    standard_deviation = float(
        noise.get(
            "standard_deviation",
            0
        )
    )

    if standard_deviation < 20:

        score = 5
        status = "Low noise variation."

    elif standard_deviation < 40:

        score = 10
        status = "Moderate noise variation."

    elif standard_deviation < 70:

        score = 15
        status = "Elevated noise variation."

    else:

        score = 18
        status = "High noise variation."

    return {
        "score": score,
        "maximum": 20,
        "status": status,
        "details": [
            "Noise standard deviation: "
            f"{standard_deviation}"
        ],
    }


def calculate_region_indicator(suspicious):
    """
    Use the existing suspicious-region indicator.
    """

    if not suspicious or not suspicious.get("success"):

        return {
            "score": 0,
            "maximum": 35,
            "status": "Region analysis unavailable.",
            "details": [],
        }

    indicator = float(
        suspicious.get(
            "indicator",
            0
        )
    )

    # Convert the existing 0-100 regional indicator
    # into the 0-35 weighted component.
    score = (
        indicator /
        100
    ) * 35

    score = round(
        clamp(score, 0, 35),
        2
    )

    region_count = int(
        suspicious.get(
            "region_count",
            0
        )
    )

    return {
        "score": score,
        "maximum": 35,
        "status": (
            f"{region_count} potentially inconsistent "
            "region(s) detected."
        ),
        "details": [
            f"Regional heuristic indicator: {indicator}/100",
            f"Detected regions: {region_count}",
        ],
    }


def determine_indicator_level(score):
    """
    Provide a descriptive level for the heuristic score.

    This is NOT an authenticity classification.
    """

    if score < 25:
        return {
            "label": "Low indicator level",
            "description": (
                "The measured signals produced relatively "
                "low heuristic responses."
            ),
        }

    if score < 50:
        return {
            "label": "Moderate indicator level",
            "description": (
                "Some measured signals produced "
                "moderate responses."
            ),
        }

    if score < 75:
        return {
            "label": "Elevated indicator level",
            "description": (
                "Several measured signals produced "
                "elevated responses and may warrant "
                "additional examination."
            ),
        }

    return {
        "label": "High indicator level",
        "description": (
            "The combined heuristic signals produced "
            "strong responses and warrant closer "
            "forensic examination."
        ),
    }


def calculate_forensic_score(
    metadata,
    ela,
    noise,
    suspicious
):
    """
    Calculate the complete transparent forensic indicator score.
    """

    metadata_result = (
        calculate_metadata_indicator(
            metadata
        )
    )

    ela_result = (
        calculate_ela_indicator(
            ela
        )
    )

    noise_result = (
        calculate_noise_indicator(
            noise
        )
    )

    region_result = (
        calculate_region_indicator(
            suspicious
        )
    )

    components = [
        {
            "name": "Metadata Indicators",
            "score": metadata_result["score"],
            "maximum": metadata_result["maximum"],
            "percentage": round(
                (
                    metadata_result["score"]
                    / metadata_result["maximum"]
                ) * 100,
                1
            ),
            "status": metadata_result["status"],
            "details": metadata_result["details"],
        },

        {
            "name": "ELA Response",
            "score": ela_result["score"],
            "maximum": ela_result["maximum"],
            "percentage": round(
                (
                    ela_result["score"]
                    / ela_result["maximum"]
                ) * 100,
                1
            ),
            "status": ela_result["status"],
            "details": ela_result["details"],
        },

        {
            "name": "Noise Variation",
            "score": noise_result["score"],
            "maximum": noise_result["maximum"],
            "percentage": round(
                (
                    noise_result["score"]
                    / noise_result["maximum"]
                ) * 100,
                1
            ),
            "status": noise_result["status"],
            "details": noise_result["details"],
        },

        {
            "name": "Regional Response",
            "score": region_result["score"],
            "maximum": region_result["maximum"],
            "percentage": round(
                (
                    region_result["score"]
                    / region_result["maximum"]
                ) * 100,
                1
            ),
            "status": region_result["status"],
            "details": region_result["details"],
        },
    ]
    total_score = sum(
        component["score"]
        for component in components
    )

    maximum_score = sum(
        component["maximum"]
        for component in components
    )

    total_score = round(
        clamp(
            total_score,
            0,
            maximum_score
        ),
        2
    )

    level = determine_indicator_level(
        total_score
    )

    return {
        "score": total_score,
        "maximum": maximum_score,
        "label": level["label"],
        "description": level["description"],
        "components": components,
    }