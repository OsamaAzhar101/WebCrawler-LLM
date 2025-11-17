import csv

from models.business import Business
from models.venue import Venue


def is_duplicate_business(business_name: str, seen_names: set) -> bool:
    return business_name in seen_names

def is_complete_business(business: dict, required_keys: list) -> bool:
    # At minimum, business should have a name
    return "name" in business and business["name"]

def save_businesses_to_csv(businesses: list, filename: str):
    if not businesses:
        print("No businesses to save.")
        return

    # Use field names from the Business model
    fieldnames = Business.model_fields.keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(businesses)
    print(f"Saved {len(businesses)} businesses to '{filename}'.")

def is_duplicate_venue(venue_name: str, seen_names: set) -> bool:
    return venue_name in seen_names


def is_complete_venue(venue: dict, required_keys: list) -> bool:
    return all(key in venue for key in required_keys)


def save_venues_to_csv(venues: list, filename: str):
    if not venues:
        print("No venues to save.")
        return

    # Use field names from the Venue model
    fieldnames = Venue.model_fields.keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(venues)
    print(f"Saved {len(venues)} venues to '{filename}'.")
