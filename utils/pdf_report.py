from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from PIL import Image as PILImage

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
)


BASE_DIR = Path(__file__).resolve().parent.parent

REPORT_FOLDER = BASE_DIR / "static" / "reports"

REPORT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


def safe_number(value, default=0):
    """
    Safely convert a value to a number for the report.
    """

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def resolve_image_path(image_path):
    """
    Resolve an image path returned by the forensic modules.

    The analysis modules may return either:
    - an absolute filesystem path
    - a relative filesystem path
    - a Flask/static URL such as /static/generated/ela.png
    - a path such as static/generated/ela.png

    ReportLab needs a real filesystem path, so convert all supported
    formats to an existing local file.
    """

    if not image_path:
        return None

    raw_path = str(image_path).strip()

    if not raw_path:
        return None

    # Ignore external URLs. The PDF generator needs local files.
    if raw_path.startswith(("http://", "https://")):
        return None

    candidates = []

    original = Path(raw_path)

    # 1. Already an absolute filesystem path.
    if original.is_absolute():
        candidates.append(original)

    # 2. Relative path from the project root.
    candidates.append(BASE_DIR / raw_path.lstrip("/\\\\ "))

    # 3. Flask/static URL or static-relative path.
    clean_path = raw_path.lstrip("/\\\\ ")
    if clean_path.startswith("static/") or clean_path.startswith("static\\"):
        candidates.append(BASE_DIR / clean_path)
    else:
        candidates.append(BASE_DIR / "static" / clean_path)

    # 4. If the module returned only a filename, check generated/.
    candidates.append(
        BASE_DIR / "static" / "generated" / Path(clean_path).name
    )

    for candidate in candidates:
        try:
            candidate = candidate.resolve()
            if candidate.exists() and candidate.is_file():
                return candidate
        except (OSError, RuntimeError):
            continue

    return None


def add_image_if_exists(
    story,
    image_path,
    width=150 * mm,
    height=None,
    max_height=95 * mm
):
    """
    Add an image while preserving its aspect ratio and keeping it
    small enough to fit on an A4 report page.
    """

    path = resolve_image_path(image_path)

    if path is None:
        return False

    try:
        with PILImage.open(path) as source_image:
            source_width, source_height = source_image.size

        if source_width <= 0 or source_height <= 0:
            return False

        if height is None:
            height = width * (source_height / source_width)

        if height > max_height:
            scale = max_height / height
            width *= scale
            height *= scale

        image = Image(
            str(path),
            width=width,
            height=height
        )

        story.append(image)
        story.append(Spacer(1, 6))

        return True

    except Exception as error:
        print(
            f"Could not add report image '{path}': {error}"
        )
        return False


def create_report(
    image_info,
    metadata,
    ela,
    noise,
    statistics,
    histogram,
    suspicious,
    forensic_score,
    original_image_path
):
    """
    Generate a complete forensic PDF report.

    This report documents the measurements produced by the
    application. It does not claim that an image is authentic
    or manipulated with certainty.
    """

    filename = image_info.get(
        "filename",
        "image"
    )

    safe_filename = Path(
        filename
    ).stem

    report_path = (
        REPORT_FOLDER /
        f"{safe_filename}_forensic_report.pdf"
    )


    document = SimpleDocTemplate(
        str(report_path),

        pagesize=A4,

        rightMargin=18 * mm,
        leftMargin=18 * mm,

        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )


    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(
        "ReportTitle",

        parent=styles["Title"],

        fontSize=22,

        leading=26,

        alignment=TA_CENTER,

        spaceAfter=12,
    )


    heading_style = ParagraphStyle(
        "ReportHeading",

        parent=styles["Heading2"],

        fontSize=16,

        leading=20,

        spaceBefore=12,

        spaceAfter=8,
    )


    subheading_style = ParagraphStyle(
        "ReportSubheading",

        parent=styles["Heading3"],

        fontSize=12,

        leading=15,

        spaceBefore=8,

        spaceAfter=6,
    )


    body_style = ParagraphStyle(
        "ReportBody",

        parent=styles["BodyText"],

        fontSize=9,

        leading=13,

        spaceAfter=6,
    )


    small_style = ParagraphStyle(
        "ReportSmall",

        parent=styles["BodyText"],

        fontSize=8,

        leading=11,

        textColor=colors.HexColor("#666666"),
    )


    story = []


    # =====================================================
    # TITLE
    # =====================================================

    story.append(
        Paragraph(
            "Digital Image Forensic Analyzer",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Digital Image Forensic Analysis Report",
            ParagraphStyle(
                "Subtitle",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                fontSize=11,
                textColor=colors.HexColor("#555555"),
                spaceAfter=18,
            )
        )
    )


    # =====================================================
    # IMAGE INFORMATION
    # =====================================================

    story.append(
        Paragraph(
            "1. Image Information",
            heading_style
        )
    )


    image_data = [
        ["Property", "Value"],

        [
            "Filename",
            str(
                image_info.get(
                    "filename",
                    "Unknown"
                )
            )
        ],

        [
            "Format",
            str(
                image_info.get(
                    "format",
                    "Unknown"
                )
            )
        ],

        [
            "Width",
            f"{image_info.get('width', 0)} px"
        ],

        [
            "Height",
            f"{image_info.get('height', 0)} px"
        ],

        [
            "Color Mode",
            str(
                image_info.get(
                    "mode",
                    "Unknown"
                )
            )
        ],

        [
            "File Size",
            f"{image_info.get('file_size', 0)} KB"
        ],
    ]


    image_table = Table(
        image_data,

        colWidths=[
            55 * mm,
            115 * mm
        ]
    )


    image_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#eef2f7")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937")
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#d9dee5")
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
            ]
        )
    )


    story.append(image_table)

    story.append(
        Spacer(1, 12)
    )


    # =====================================================
    # ORIGINAL IMAGE
    # =====================================================

    story.append(
        Paragraph(
            "Original Image",
            subheading_style
        )
    )


    add_image_if_exists(
        story,
        original_image_path,
        width=150 * mm
    )


    # =====================================================
    # FORENSIC INDICATOR SCORE
    # =====================================================

    story.append(
        Paragraph(
            "2. Forensic Indicator Summary",
            heading_style
        )
    )


    total_score = forensic_score.get(
        "score",
        0
    )

    maximum_score = forensic_score.get(
        "maximum",
        100
    )

    indicator_label = forensic_score.get(
        "label",
        "Unavailable"
    )


    story.append(
        Paragraph(
            f"<b>Indicator Score:</b> "
            f"{total_score} / {maximum_score}",
            body_style
        )
    )


    story.append(
        Paragraph(
            f"<b>Indicator Level:</b> "
            f"{indicator_label}",
            body_style
        )
    )


    story.append(
        Paragraph(
            forensic_score.get(
                "description",
                ""
            ),
            body_style
        )
    )


    components = forensic_score.get(
        "components",
        []
    )


    if components:

        score_data = [
            [
                "Component",
                "Score",
                "Maximum",
                "Percentage"
            ]
        ]


        for component in components:

            score = safe_number(
                component.get(
                    "score",
                    0
                )
            )

            maximum = safe_number(
                component.get(
                    "maximum",
                    0
                )
            )

            percentage = safe_number(
                component.get(
                    "percentage",
                    0
                )
            )


            score_data.append(
                [
                    component.get(
                        "name",
                        ""
                    ),

                    f"{score:g}",

                    f"{maximum:g}",

                    f"{percentage:g}%"
                ]
            )


        score_table = Table(
            score_data,

            colWidths=[
                75 * mm,
                30 * mm,
                30 * mm,
                35 * mm
            ]
        )


        score_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#eef2f7")
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#d9dee5")
                    ),

                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                ]
            )
        )


        story.append(score_table)


    # =====================================================
    # METADATA
    # =====================================================

    story.append(
        Paragraph(
            "3. Metadata Analysis",
            heading_style
        )
    )


    metadata_fields = metadata.get(
        "fields",
        {}
    ) if metadata else {}


    if metadata_fields:

        metadata_data = [
            ["Field", "Value"]
        ]


        for key, value in metadata_fields.items():

            # Some EXIF fields contain binary/encoded data rather than
            # readable text. Avoid printing unreadable characters in PDF.
            if isinstance(value, bytes):
                display_value = "Binary/encoded data"
            else:
                display_value = str(value)

                if (
                    "\x00" in display_value
                    or "\ufffd" in display_value
                    or any(
                        ord(char) < 32
                        and char not in "\\t\\n\\r"
                        for char in display_value
                    )
                ):
                    display_value = "Binary/encoded data"

            metadata_data.append(
                [
                    str(key),
                    display_value
                ]
            )


        metadata_table = Table(
            metadata_data,

            colWidths=[
                60 * mm,
                110 * mm
            ]
        )


        metadata_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#eef2f7")
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#d9dee5")
                    ),

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),

                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                ]
            )
        )


        story.append(
            metadata_table
        )

    else:

        story.append(
            Paragraph(
                "No readable EXIF metadata was found.",
                body_style
            )
        )


    # =====================================================
    # ELA
    # =====================================================

    story.append(
        PageBreak()
    )


    story.append(
        Paragraph(
            "4. Error Level Analysis",
            heading_style
        )
    )


    if ela and ela.get("success"):

        ela_data = [
            ["Measurement", "Value"],

            [
                "Analysis Width",
                f"{ela.get('width', 0)} px"
            ],

            [
                "Analysis Height",
                f"{ela.get('height', 0)} px"
            ],

            [
                "JPEG Quality",
                str(
                    ela.get(
                        "jpeg_quality",
                        ""
                    )
                )
            ],

            [
                "Maximum Difference",
                str(
                    ela.get(
                        "maximum_difference",
                        ""
                    )
                )
            ],

            [
                "Average Difference",
                str(
                    ela.get(
                        "average_difference",
                        ""
                    )
                )
            ],
        ]


        ela_table = Table(
            ela_data,

            colWidths=[
                65 * mm,
                105 * mm
            ]
        )


        ela_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#eef2f7")
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#d9dee5")
                    ),

                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                ]
            )
        )


        story.append(
            ela_table
        )


        story.append(
            Spacer(1, 10)
        )


        story.append(
            Paragraph(
                "ELA Visualization",
                subheading_style
            )
        )


        ela_image_added = add_image_if_exists(
            story,
            ela.get("path"),
            width=150 * mm
        )

        if not ela_image_added:
            story.append(
                Paragraph(
                    "ELA visualization image was not found.",
                    small_style
                )
            )


        story.append(
            Paragraph(
                "ELA highlights regions that respond differently "
                "to JPEG recompression. Differences can have many "
                "causes and should not be interpreted as conclusive "
                "proof of manipulation.",
                small_style
            )
        )

    else:

        story.append(
            Paragraph(
                "ELA analysis was not available.",
                body_style
            )
        )


    # =====================================================
    # NOISE
    # =====================================================

    story.append(
        PageBreak()
    )


    story.append(
        Paragraph(
            "5. Noise Analysis",
            heading_style
        )
    )


    if noise and noise.get("success"):

        noise_data = [
            ["Measurement", "Value"],

            [
                "Analysis Width",
                f"{noise.get('width', 0)} px"
            ],

            [
                "Analysis Height",
                f"{noise.get('height', 0)} px"
            ],

            [
                "Mean Noise",
                str(
                    noise.get(
                        "mean",
                        ""
                    )
                )
            ],

            [
                "Standard Deviation",
                str(
                    noise.get(
                        "standard_deviation",
                        ""
                    )
                )
            ],

            [
                "Maximum Noise",
                str(
                    noise.get(
                        "maximum",
                        ""
                    )
                )
            ],
        ]


        noise_table = Table(
            noise_data,

            colWidths=[
                65 * mm,
                105 * mm
            ]
        )


        noise_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#eef2f7")
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#d9dee5")
                    ),

                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                ]
            )
        )


        story.append(
            noise_table
        )


        story.append(
            Spacer(1, 10)
        )


        story.append(
            Paragraph(
                "Noise Map",
                subheading_style
            )
        )


        noise_image_added = add_image_if_exists(
            story,
            noise.get("path"),
            width=150 * mm
        )

        if not noise_image_added:
            story.append(
                Paragraph(
                    "Noise map image was not found.",
                    small_style
                )
            )


        story.append(
            Paragraph(
                "Noise variation can be influenced by texture, "
                "edges, lighting, camera processing and compression. "
                "It is therefore an indicator rather than conclusive "
                "evidence of manipulation.",
                small_style
            )
        )

    else:

        story.append(
            Paragraph(
                "Noise analysis was not available.",
                body_style
            )
        )


    # =====================================================
    # IMAGE STATISTICS
    # =====================================================

    story.append(
        PageBreak()
    )


    story.append(
        Paragraph(
            "6. Image Statistics",
            heading_style
        )
    )


    if statistics and statistics.get("success"):

        statistics_data = [
            ["Measurement", "Value"],

            [
                "Brightness",
                str(
                    statistics.get(
                        "brightness",
                        ""
                    )
                )
            ],

            [
                "Contrast",
                str(
                    statistics.get(
                        "contrast",
                        ""
                    )
                )
            ],

            [
                "Mean Intensity",
                str(
                    statistics.get(
                        "mean_intensity",
                        ""
                    )
                )
            ],

            [
                "Standard Deviation",
                str(
                    statistics.get(
                        "standard_deviation",
                        ""
                    )
                )
            ],

            [
                "Minimum Intensity",
                str(
                    statistics.get(
                        "minimum_intensity",
                        ""
                    )
                )
            ],

            [
                "Maximum Intensity",
                str(
                    statistics.get(
                        "maximum_intensity",
                        ""
                    )
                )
            ],

            [
                "Entropy",
                str(
                    statistics.get(
                        "entropy",
                        ""
                    )
                )
            ],
        ]


        statistics_table = Table(
            statistics_data,

            colWidths=[
                65 * mm,
                105 * mm
            ]
        )


        statistics_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#eef2f7")
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#d9dee5")
                    ),

                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                ]
            )
        )


        story.append(
            statistics_table
        )

    else:

        story.append(
            Paragraph(
                "Image statistics were not available.",
                body_style
            )
        )


    # =====================================================
    # HISTOGRAMS
    # =====================================================

    story.append(
        PageBreak()
    )


    story.append(
        Paragraph(
            "7. Histogram Analysis",
            heading_style
        )
    )


    if histogram and histogram.get("success"):

        story.append(
            Paragraph(
                "RGB Histogram",
                subheading_style
            )
        )


        rgb_image_added = add_image_if_exists(
            story,
            histogram.get("rgb_path"),
            width=150 * mm
        )

        if not rgb_image_added:
            story.append(
                Paragraph(
                    "RGB histogram image was not found.",
                    small_style
                )
            )


        story.append(
            Paragraph(
                "Grayscale Histogram",
                subheading_style
            )
        )


        grayscale_image_added = add_image_if_exists(
            story,
            histogram.get("grayscale_path"),
            width=150 * mm
        )

        if not grayscale_image_added:
            story.append(
                Paragraph(
                    "Grayscale histogram image was not found.",
                    small_style
                )
            )


        story.append(
            Paragraph(
                "Histograms represent the distribution of pixel "
                "intensities. They can help characterize exposure, "
                "contrast and tonal distribution.",
                small_style
            )
        )

    else:

        story.append(
            Paragraph(
                "Histogram analysis was not available.",
                body_style
            )
        )


    # =====================================================
    # SUSPICIOUS REGIONS
    # =====================================================

    story.append(
        PageBreak()
    )


    story.append(
        Paragraph(
            "8. Potentially Inconsistent Regions",
            heading_style
        )
    )


    if suspicious and suspicious.get("success"):

        region_count = suspicious.get(
            "region_count",
            0
        )

        indicator = suspicious.get(
            "indicator",
            0
        )

        threshold = suspicious.get(
            "threshold",
            0
        )


        story.append(
            Paragraph(
                f"<b>Detected Regions:</b> {region_count}",
                body_style
            )
        )


        story.append(
            Paragraph(
                f"<b>Regional Indicator:</b> {indicator}",
                body_style
            )
        )


        story.append(
            Paragraph(
                f"<b>Detection Threshold:</b> {threshold}",
                body_style
            )
        )


        story.append(
            Paragraph(
                "Potential Region Heatmap",
                subheading_style
            )
        )


        heatmap_image_added = add_image_if_exists(
            story,
            suspicious.get(
                "heatmap_path"
            ),
            width=150 * mm
        )

        if not heatmap_image_added:
            story.append(
                Paragraph(
                    "Potential region heatmap image was not found.",
                    small_style
                )
            )


        story.append(
            Paragraph(
                "Detected Region Overlay",
                subheading_style
            )
        )


        overlay_image_added = add_image_if_exists(
            story,
            suspicious.get(
                "overlay_path"
            ),
            width=150 * mm
        )

        if not overlay_image_added:
            story.append(
                Paragraph(
                    "Detected region overlay image was not found.",
                    small_style
                )
            )


        story.append(
            Paragraph(
                "Detected regions represent areas with stronger "
                "responses from the application's heuristic "
                "analysis. Natural image characteristics can also "
                "produce such responses.",
                small_style
            )
        )

    else:

        story.append(
            Paragraph(
                "Potentially inconsistent region analysis "
                "was not available.",
                body_style
            )
        )


    # =====================================================
    # FINAL DISCLAIMER
    # =====================================================

    story.append(
        PageBreak()
    )


    story.append(
        Paragraph(
            "9. Interpretation and Limitations",
            heading_style
        )
    )


    story.append(
        Paragraph(
            "This report summarizes measurements produced by "
            "the Digital Image Forensic Analyzer. The forensic "
            "indicator score is a rule-based heuristic and is "
            "not a probability of image manipulation.",
            body_style
        )
    )


    story.append(
        Paragraph(
            "ELA, noise analysis, metadata, histograms, "
            "statistics and regional analysis can provide useful "
            "forensic indicators, but none of these measurements "
            "should independently be treated as conclusive proof "
            "that an image has been manipulated.",
            body_style
        )
    )


    story.append(
        Paragraph(
            "For reliable forensic conclusions, results should "
            "be interpreted alongside the original evidence, "
            "source information and, where appropriate, additional "
            "forensic examination.",
            body_style
        )
    )


    story.append(
        Spacer(1, 15)
    )


    story.append(
        Paragraph(
            "Generated by Digital Image Forensic Analyzer",
            small_style
        )
    )


    # =====================================================
    # BUILD PDF
    # =====================================================

    document.build(
        story
    )


    return report_path