import json


def load_json(json_filename: str) -> dict:
    """Load a JSON file and return its content as a Python object."""

    with open(json_filename, "r") as file:
        data = json.load(file)

    return data


def json_extract_info(json_data: list) -> tuple:
    """Extract specific information from the JSON data.

    Args:
        json_data : list : List of JSON data.

    Returns:
        tuple : Tuple containing lists of extracted information.
    """
    extracted_rating = []
    extracted_average_median = []
    extracted_min_max_peak = []
    extracted_background_noise = []
    extracted_dominant_noise = []
    for item in json_data:
        rating = {
            "timestamp": item.get("timestamp"),
            "rating": item.get("LAeq_rating"),
        }
        average_median = {
            "timestamp": item.get("timestamp"),
            "average_dB": item.get("LAeq_segment_dB"),
            "median_dB": item.get("L50_dB"),
        }
        min_max_peak = {
            "timestamp": item.get("timestamp"),
            "min_dB": item.get("Lmin_dB"),
            "max_dB": item.get("Lmax_dB"),
            "peak_dB": item.get("LPeak_dB"),
        }
        background_noise = {
            "timestamp": item.get("timestamp"),
            "background_noise_dB": item.get("L90_dB"),
        }
        dominant_noise = {
            "timestamp": item.get("timestamp"),
            "dominant_noise_type": item.get("top_5_labels")[0],
        }
        extracted_rating.append(rating)
        extracted_average_median.append(average_median)
        extracted_min_max_peak.append(min_max_peak)
        extracted_background_noise.append(background_noise)
        extracted_dominant_noise.append(dominant_noise)

    return (
        extracted_rating,
        extracted_dominant_noise,
        extracted_average_median,
        extracted_min_max_peak,
        extracted_background_noise,
    )


def get_average_rating(ratings: list) -> str:
    """Calculate the average rating from the JSON data.

    Args:
        ratings : list : List of ratings extracted from JSON data.

    Returns:
        str : Average rating as a letter (A-G).
    """
    rating_values = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}

    numeric_ratings = []
    for rating in ratings:
        if rating["rating"] in rating_values:
            numeric_ratings.append(rating_values[rating["rating"]])

    if not numeric_ratings:
        return "N/A"

    avg_numeric = sum(numeric_ratings) / len(numeric_ratings)

    reverse_ratings = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F", 7: "G"}
    return reverse_ratings.get(round(avg_numeric), "N/A")


def get_noise_type_by_hour(extracted_dominant_noise: list) -> dict:
    """Get noise types grouped by hour.

    Args:
        extracted_dominant_noise : list : List of dominant noise types extracted from JSON data.
    Returns:
        dict : Dictionary with hour as keys and list of noise types as values.
            Exemple :
            {"10": ["traffic", "construction", "traffic"],
            "11": ["nature", "traffic"]}
    """

    noise_type_by_hour = {}
    for item in extracted_dominant_noise:
        timestamp = item.get("timestamp")
        hour = timestamp.split(" ")[1].split(":")[0]
        noise_type = item.get("dominant_noise_type")
        if hour not in noise_type_by_hour:
            noise_type_by_hour[hour] = []
        noise_type_by_hour[hour].append(noise_type)
    return noise_type_by_hour


def get_noise_type_db_hourly(noise_type_by_hour: dict) -> dict:
    """Get the most common noise type per hour with its percentage.

    Args:
        noise_type_by_hour : dict : Dictionary of noise types by hour.

    Returns:
        dict : Dictionary with hour as keys and most common noise type with percentage as values.
            Exemple :
            {"10": {"noise_type": "traffic", "percentage": 70.0},
            "11": {"noise_type": "construction", "percentage": 60.0}}
    """
    dominant_noise_hourly = {}

    for hour, noise_types in noise_type_by_hour.items():
        noise_type_count = {}
        total_count = len(noise_types)

        for noise_type in noise_types:
            if noise_type in noise_type_count:
                noise_type_count[noise_type] += 1
            else:
                noise_type_count[noise_type] = 1

        most_common = max(noise_type_count, key=noise_type_count.get)
        percentage = round((noise_type_count[most_common] / total_count) * 100, 1)

        dominant_noise_hourly[hour] = {
            "noise_type": most_common,
            "percentage": percentage,
        }

    return dominant_noise_hourly


def get_noise_type_percentage_daily(extracted_dominant_noise: list) -> dict:
    """Calculate the percentage of each noise type in the JSON data.

    Args :
        extracted_dominant_noise : list : List of dominant noise types extracted from JSON data.

    Returns:
        dict : Dictionary with noise types as keys and their percentage as values.
            Exemple :
            {"traffic": 45.5,
            "construction": 30.0,
            "nature": 24.5}
    """
    noise_type_count = {}
    total_count = len(extracted_dominant_noise)

    for item in extracted_dominant_noise:
        noise_type = item.get("dominant_noise_type") if isinstance(item, dict) else item
        if noise_type in noise_type_count:
            noise_type_count[noise_type] += 1
        else:
            noise_type_count[noise_type] = 1

    noise_type_percentage = {
        noise_type: round((count / total_count) * 100, 1)
        for noise_type, count in noise_type_count.items()
    }
    
    sorted_items = sorted(noise_type_percentage.items(), key=lambda x: x[1], reverse=True)
    top_5 = dict(sorted_items[:5])

    return top_5


def get_average_db(extracted_average_median: list) -> float:
    """Calculate the average dB from the JSON data.

    Args:
        extracted_average_median : list : List of average and median dB values extracted from JSON
    Returns:
        float : Average dB value.
    """
    total_db = 0
    count = 0

    for item in extracted_average_median:
        avg_db = item.get("average_dB")
        if avg_db is not None:
            total_db += avg_db
            count += 1

    if count == 0:
        return 0

    return round(total_db / count, 1)


if __name__ == "__main__":
    data = load_json("./dps_analysis_pi3_exemple.json")
    print(len(data))
    (
        extracted_rating,
        extracted_dominant_noise,
        extracted_average_median,
        extracted_min_max_peak,
        extracted_background_noise,
    ) = json_extract_info(data)

    average_db = get_average_db(extracted_average_median)
    print("Average dB per day:", average_db)

    average_rating = get_average_rating(extracted_rating)
    print("Average Rating daily:", average_rating)

    noise_percentage = get_noise_type_percentage_daily(extracted_dominant_noise)
    print("Noise Type daily Percentage :", noise_percentage)

    noise_by_hour = get_noise_type_by_hour(extracted_dominant_noise)

    noise_percentage_hourly = get_noise_type_percentage_hourly(noise_by_hour)
    print("Noise Type Percentage Hourly:", noise_percentage_hourly["10"])
