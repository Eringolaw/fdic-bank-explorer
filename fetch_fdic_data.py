#!/usr/bin/env python3
"""
FDIC Bank Data Fetcher
Retrieves all FDIC-insured banks and branch locations from the FDIC BankFind API.

API Documentation: https://api.fdic.gov/banks/docs/
"""

import requests
import json
import csv
import time
from pathlib import Path

BASE_URL = "https://api.fdic.gov/banks"

# Key fields to retrieve for institutions
INSTITUTION_FIELDS = [
    "CERT",        # FDIC Certificate Number (unique identifier)
    "NAME",        # Institution name
    "CITY",        # City
    "STNAME",      # State name
    "ZIP",         # ZIP code
    "ADDRESS",     # Street address
    "BKCLASS",     # Institution class
    "CHARTER",     # Charter type
    "ACTIVE",      # Active status
    "INSDATE",     # Insurance date
    "REGAGENT",    # Regulatory agent
    "ASSET",       # Total assets (if available)
    "DEP",         # Total deposits (if available)
    "LATITUDE",    # Latitude
    "LONGITUDE",   # Longitude
    "WEBADDR",     # Website
]

# Key fields to retrieve for locations/branches
LOCATION_FIELDS = [
    "CERT",        # FDIC Certificate Number (links to institution)
    "UNINUM",      # Unique branch identifier
    "NAME",        # Institution name
    "OFFNAME",     # Branch/office name
    "OFFNUM",      # Office number
    "ADDRESS",     # Street address
    "CITY",        # City
    "STNAME",      # State name
    "ZIP",         # ZIP code
    "COUNTY",      # County
    "SERVTYPE_DESC",  # Service type description
    "MAINOFF",     # Main office flag
    "ESTYMD",      # Establishment date
    "LATITUDE",    # Latitude
    "LONGITUDE",   # Longitude
]


def fetch_all_records(endpoint: str, fields: list, filters: str = None, limit: int = 10000) -> list:
    """
    Fetch all records from an FDIC API endpoint with pagination.

    Args:
        endpoint: API endpoint ('institutions' or 'locations')
        fields: List of fields to retrieve
        filters: Optional filter string using Elasticsearch query syntax
        limit: Records per request (max 10000)

    Returns:
        List of all records
    """
    all_records = []
    offset = 0

    # First, get the total count
    params = {
        "limit": 1,
        "fields": ",".join(fields),
    }
    if filters:
        params["filters"] = filters

    response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
    response.raise_for_status()
    data = response.json()

    total = data["meta"]["total"]
    print(f"Total {endpoint} records to fetch: {total:,}")

    # Fetch all records with pagination
    while offset < total:
        params = {
            "limit": limit,
            "offset": offset,
            "fields": ",".join(fields),
        }
        if filters:
            params["filters"] = filters

        print(f"Fetching {endpoint} records {offset:,} - {min(offset + limit, total):,}...")

        response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()

        records = [item["data"] for item in data["data"]]
        all_records.extend(records)

        offset += limit

        # Be respectful to the API
        time.sleep(0.5)

    print(f"Fetched {len(all_records):,} {endpoint} records total.\n")
    return all_records


def save_to_csv(records: list, filename: str, fields: list):
    """Save records to a CSV file."""
    if not records:
        print(f"No records to save for {filename}")
        return

    filepath = Path(filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)

    print(f"Saved {len(records):,} records to {filepath}")


def save_to_json(records: list, filename: str):
    """Save records to a JSON file."""
    filepath = Path(filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    print(f"Saved {len(records):,} records to {filepath}")


def main():
    print("=" * 60)
    print("FDIC Bank Data Fetcher")
    print("=" * 60)
    print()

    # Fetch all FDIC-insured institutions
    # Filter for active, FDIC-insured institutions
    print("Fetching FDIC-insured institutions...")
    institutions = fetch_all_records(
        endpoint="institutions",
        fields=INSTITUTION_FIELDS,
        filters="ACTIVE:1",  # Only active institutions
    )

    # Save institutions
    save_to_csv(institutions, "fdic_institutions.csv", INSTITUTION_FIELDS)
    save_to_json(institutions, "fdic_institutions.json")

    print()

    # Fetch all branch locations
    print("Fetching bank branch locations...")
    locations = fetch_all_records(
        endpoint="locations",
        fields=LOCATION_FIELDS,
    )

    # Save locations
    save_to_csv(locations, "fdic_locations.csv", LOCATION_FIELDS)
    save_to_json(locations, "fdic_locations.json")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total institutions: {len(institutions):,}")
    print(f"Total branch locations: {len(locations):,}")
    print()
    print("Files created:")
    print("  - fdic_institutions.csv / .json")
    print("  - fdic_locations.csv / .json")


if __name__ == "__main__":
    main()
