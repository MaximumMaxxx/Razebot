import requests


CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")
valid_ranks = []
for i in CompTiers.json()["data"][0]["tiers"]:
    # Just making sure that it's not one of the unused divisions
    if not i["divisionName"].lower() in valid_ranks and i["divisionName"] != "Unused2" and i["divisionName"] != "Unused1":
        # valid_ranks should have the lowercase version of the ranks
        valid_ranks.append(i["divisionName"].lower())