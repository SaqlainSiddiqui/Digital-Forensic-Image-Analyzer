import os
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)

from PIL import Image, UnidentifiedImageError

from werkzeug.utils import secure_filename


# =========================================================
# FORENSIC MODULES
# =========================================================

from forensic.metadata import analyze_metadata

from forensic.ela import perform_ela

from forensic.noise import analyze_noise

from forensic.statistics import calculate_statistics

from forensic.histogram import generate_histogram

from forensic.suspicious_regions import (
    detect_suspicious_regions
)


# =========================================================
# UTILITY MODULES
# =========================================================

from utils.scoring import calculate_forensic_score

from utils.pdf_report import create_report


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / "uploads"

GENERATED_FOLDER = (
    BASE_DIR /
    "static" /
    "generated"
)

REPORT_FOLDER = (
    BASE_DIR /
    "static" /
    "reports"
)


# =========================================================
# FILE SETTINGS
# =========================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "bmp",
    "webp",
}


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)


# Used by Flask for flash messages
app.secret_key = "change-this-secret-key"


app.config["UPLOAD_FOLDER"] = str(
    UPLOAD_FOLDER
)

app.config["MAX_CONTENT_LENGTH"] = (
    MAX_FILE_SIZE
)


# =========================================================
# CREATE REQUIRED DIRECTORIES
# =========================================================

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


GENERATED_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


REPORT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_file(filename):
    """
    Check whether the uploaded file has an
    allowed extension.
    """

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


def get_file_size(file_path):
    """
    Return file size in KB.
    """

    size_bytes = os.path.getsize(
        file_path
    )

    return round(
        size_bytes / 1024,
        2
    )


# =========================================================
# MAIN ROUTE
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    # -----------------------------------------------------
    # GET REQUEST
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "index.html"
        )


    # -----------------------------------------------------
    # CHECK UPLOAD
    # -----------------------------------------------------

    if "image" not in request.files:

        flash(
            "No image was uploaded.",
            "error"
        )

        return redirect(
            url_for("index")
        )


    file = request.files["image"]


    # -----------------------------------------------------
    # CHECK EMPTY FILE
    # -----------------------------------------------------

    if file.filename == "":

        flash(
            "Please select an image.",
            "error"
        )

        return redirect(
            url_for("index")
        )


    # -----------------------------------------------------
    # CHECK FILE EXTENSION
    # -----------------------------------------------------

    if not allowed_file(
        file.filename
    ):

        flash(
            (
                "Invalid file type. "
                "Allowed formats: "
                "JPG, JPEG, PNG, BMP, WEBP."
            ),
            "error",
        )

        return redirect(
            url_for("index")
        )


    # -----------------------------------------------------
    # SECURE FILENAME
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )


    if not filename:

        flash(
            "Invalid filename.",
            "error"
        )

        return redirect(
            url_for("index")
        )


    # -----------------------------------------------------
    # SAVE UPLOADED IMAGE
    # -----------------------------------------------------

    file_path = (
        UPLOAD_FOLDER /
        filename
    )


    file.save(
        file_path
    )


    # -----------------------------------------------------
    # IMAGE PROCESSING
    # -----------------------------------------------------

    try:

        # =================================================
        # VERIFY IMAGE
        # =================================================

        with Image.open(
            file_path
        ) as image:

            image.verify()


        # =================================================
        # READ IMAGE INFORMATION
        # =================================================

        with Image.open(
            file_path
        ) as image:

            width, height = image.size

            image_format = image.format

            mode = image.mode


        file_size = get_file_size(
            file_path
        )


        # =================================================
        # IMAGE INFORMATION
        # =================================================
        #
        # IMPORTANT:
        # This MUST be created before the PDF report.
        # =================================================

        image_info = {

            "filename": filename,

            "format": image_format,

            "width": width,

            "height": height,

            "mode": mode,

            "file_size": file_size,

            "path": url_for(
                "uploaded_file",
                filename=filename
            ),
        }


        # =================================================
        # 1. METADATA ANALYSIS
        # =================================================

        metadata = analyze_metadata(
            file_path
        )


        # =================================================
        # 2. ERROR LEVEL ANALYSIS
        # =================================================

        ela_result = perform_ela(
            file_path,
            GENERATED_FOLDER
        )


        # =================================================
        # 3. NOISE ANALYSIS
        # =================================================

        noise_result = analyze_noise(
            file_path,
            GENERATED_FOLDER
        )


        # =================================================
        # 4. IMAGE STATISTICS
        # =================================================

        statistics_result = calculate_statistics(
            file_path
        )


        # =================================================
        # 5. HISTOGRAM ANALYSIS
        # =================================================

        histogram_result = generate_histogram(
            file_path,
            GENERATED_FOLDER
        )


        # =================================================
        # 6. SUSPICIOUS REGION ANALYSIS
        # =================================================

        suspicious_result = detect_suspicious_regions(
            file_path,
            GENERATED_FOLDER
        )


        # =================================================
        # 7. FORENSIC INDICATOR SCORE
        # =================================================

        forensic_score = calculate_forensic_score(
            metadata,
            ela_result,
            noise_result,
            suspicious_result
        )


        # =================================================
        # 8. GENERATE PDF REPORT
        # =================================================

        report_path = create_report(

            image_info=image_info,

            metadata=metadata,

            ela=ela_result,

            noise=noise_result,

            statistics=statistics_result,

            histogram=histogram_result,

            suspicious=suspicious_result,

            forensic_score=forensic_score,

            original_image_path=file_path
        )


        # =================================================
        # PDF REPORT URL
        # =================================================

        report_url = url_for(
            "static",
            filename=(
                f"reports/{report_path.name}"
            )
        )


        # =================================================
        # DISPLAY COMPLETE ANALYSIS
        # =================================================

        return render_template(

            "index.html",

            image_info=image_info,

            metadata=metadata,

            ela=ela_result,

            noise=noise_result,

            statistics=statistics_result,

            histogram=histogram_result,

            suspicious=suspicious_result,

            forensic_score=forensic_score,

            report_url=report_url
        )


    # =====================================================
    # INVALID IMAGE
    # =====================================================

    except UnidentifiedImageError:

        if file_path.exists():

            file_path.unlink()


        flash(
            "The uploaded file is not a valid image.",
            "error"
        )


        return redirect(
            url_for("index")
        )


    # =====================================================
    # OTHER PROCESSING ERROR
    # =====================================================

    except Exception as error:

        if file_path.exists():

            file_path.unlink()


        print(
            "Image processing error:",
            error
        )


        flash(
            (
                "Something went wrong while "
                "processing the image."
            ),
            "error",
        )


        return redirect(
            url_for("index")
        )


# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    return render_template(

        "index.html",

        error_message=(
            "File is too large. "
            "Maximum allowed size is 10 MB."
        ),

    ), 413


# =========================================================
# SERVE UPLOADED IMAGES
# =========================================================

@app.route(
    "/uploads/<filename>"
)
def uploaded_file(filename):

    return send_from_directory(

        app.config["UPLOAD_FOLDER"],

        filename
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )