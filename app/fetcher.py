import requests
from config import  PER_PAGE, REQUEST_TIMEOUT, HEADERS,REQUEST_DELAY
import time


def fetch_json_from_api(base_url):
    page = 1
    all_properties = []

    while True:
        print(f"Fetching page {page}...")

        response = requests.get(
            base_url,
            params={
                "per_page": PER_PAGE,
                "page": page
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        # Stop if page out of range (WordPress returns 400)
        if response.status_code == 400:
            print("No more pages. Stopping pagination.")
            break

        # Stop on any unexpected error
        if response.status_code != 200:
            print(f"Error on page {page}: {response.status_code}")
            break

        data = response.json()

        print(f"Page {page} returned {len(data)} records.")

        # Safety stop if somehow empty
        if not data:
            break

        all_properties.extend(data)
        page += 1
        time.sleep(REQUEST_DELAY)

    print(f"Total properties fetched: {len(all_properties)}")

    return all_properties
