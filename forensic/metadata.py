from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def convert_gps_to_degrees(value):
    """
    Convert GPS coordinates from EXIF format to decimal degrees.
    """

    try:
        degrees = float(value[0])
        minutes = float(value[1])
        seconds = float(value[2])

        return degrees + (minutes / 60) + (seconds / 3600)

    except (TypeError, ValueError, IndexError, ZeroDivisionError):
        return None


def extract_gps_data(exif_data):
    """
    Extract GPS information from EXIF metadata.
    """

    gps_info = exif_data.get(34853)

    if not gps_info:
        return None

    gps_data = {}

    for key, value in gps_info.items():
        tag_name = GPSTAGS.get(key, key)
        gps_data[tag_name] = value

    latitude = gps_data.get("GPSLatitude")
    latitude_ref = gps_data.get("GPSLatitudeRef")

    longitude = gps_data.get("GPSLongitude")
    longitude_ref = gps_data.get("GPSLongitudeRef")

    latitude_decimal = None
    longitude_decimal = None

    if latitude:
        latitude_decimal = convert_gps_to_degrees(latitude)

        if latitude_ref == "S":
            latitude_decimal = -latitude_decimal

    if longitude:
        longitude_decimal = convert_gps_to_degrees(longitude)

        if longitude_ref == "W":
            longitude_decimal = -longitude_decimal

    if latitude_decimal is None or longitude_decimal is None:
        return None

    return {
        "latitude": latitude_decimal,
        "longitude": longitude_decimal,
    }


def analyze_metadata(image_path):
    """
    Extract and organize EXIF metadata from an image.
    """

    metadata = {
        "has_exif": False,
        "fields": {},
        "gps": None,
    }

    try:

        with Image.open(image_path) as image:

            exif = image.getexif()

            if not exif:
                return metadata

            metadata["has_exif"] = True

            for tag_id, value in exif.items():

                tag_name = TAGS.get(tag_id, str(tag_id))

                # Convert certain Pillow objects to strings
                try:
                    if isinstance(value, bytes):
                        value = value.decode(
                            "utf-8",
                            errors="replace"
                        )

                    else:
                        value = str(value)

                except Exception:
                    value = str(value)

                metadata["fields"][tag_name] = value

            metadata["gps"] = extract_gps_data(exif)

    except Exception as error:

        metadata["error"] = str(error)

    return metadata