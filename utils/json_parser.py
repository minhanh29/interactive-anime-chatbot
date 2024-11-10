import yaml


def parse_json(json_str, marker="{}"):
    indx = json_str.rfind(marker[1])
    json_str = json_str[:indx+1]

    try:
        return yaml.safe_load(json_str)
    except:
        print("Level 2. Cannot parse json. Refining it...")

    indx = json_str.find(marker[0])
    json_str = json_str[indx:]
    try:
        return yaml.safe_load(json_str)
    except:
        print("Level 2. Cannot parse json. Refining it...")

    return None
