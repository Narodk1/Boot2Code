import json

def load_json(json_filename: str):
    """Load a JSON file and return its content as a Python object."""

    with open(json_filename, 'r') as file:
        data = json.load(file)
    
    return data


if __name__ == "__main__":
    data = load_json("./dps_analysis_pi3_exemple.json")
    print(len(data))
