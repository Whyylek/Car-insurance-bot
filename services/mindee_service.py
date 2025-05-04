import requests
import json
import time

def extract_passport_data(image_bytes, api_key):
    """
    Sends a passport image to the Mindee API for data extraction.
    Returns the full JSON response if successful, or None on failure.
    
    :param image_bytes: Image file in bytes
    :param api_key: Mindee API key
    :return: Parsed JSON response or None
    """

    url = "https://api.mindee.net/v1/products/mindee/passport/v1/predict"
    headers = {"Authorization": f"Token {api_key}"}
    files = {"document": image_bytes}

    # Check for missing API key
    if not api_key:
        print("[Mindee] Error: API Key is missing")
        return None

    try:
        # Send request to Mindee Passport API
        response = requests.post(url, headers=headers, files=files)
        print(f"[Mindee] Status Code: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            prediction = (
                data.get("document", {})
                .get("inference", {})
                .get("prediction", {})
            )

            # Validate that at least the surname was found
            surname_data = prediction.get("surname", {})
            if not surname_data.get("value"):
                print("[Mindee] Error: No valid surname found in prediction")
                return None

            return data  # Return full response for flexibility
        else:
            error_msg = response.json().get("api_request", {}).get("error", {}).get("message", "Unknown error")
            print(f"[Mindee] API Error: {error_msg}")
            return None
    except Exception as e:
        print(f"[Mindee] Network/Error: {e}")
        return None


def extract_vehicle_data(image_bytes, api_key):
    """
    Submits a vehicle document to Mindee for async processing.
    Waits for result by polling and returns structured vehicle data.

    :param image_bytes: Image file in bytes
    :param api_key: Mindee API key
    :return: Dictionary with extracted vehicle info or None
    """

    url = "https://api.mindee.net/v1/products/Whylek/vehicle_registration/v1/predict_async"
    headers = {"Authorization": f"Token {api_key}"}
    files = {"document": image_bytes}

    if not api_key:
        print("[Mindee Vehicle] Error: API Key is missing")
        return None

    try:
        # Submit the document for async processing
        response = requests.post(url, headers=headers, files=files)
        print(f"[Mindee Vehicle] Submit Status Code: {response.status_code}")

        if response.status_code != 202:
            error_msg = response.json().get("api_request", {}).get("error", {}).get("message", "Unknown error")
            print(f"[Mindee Vehicle] API Error: {error_msg}")
            return None

        # Extract job ID and polling URL from response
        job_data = response.json()
        job_id = job_data.get("job", {}).get("id")
        polling_url = job_data.get("job", {}).get("polling_url")

        if not job_id or not polling_url:
            print("[Mindee Vehicle] Error: No job ID or polling URL returned")
            return None

        # Poll for result until completion or timeout
        return poll_for_vehicle_result(polling_url, api_key)

    except Exception as e:
        print(f"[Mindee Vehicle] Network/Error: {e}")
        return None


def poll_for_vehicle_result(polling_url, api_key):
    """
    Polls the given URL periodically to check the status of an async vehicle document job.
    Returns parsed vehicle data when available.

    :param polling_url: URL provided by initial async call
    :param api_key: Mindee API key
    :return: Dictionary with vin, license_plate, make, model or None
    """

    headers = {"Authorization": f"Token {api_key}"}

    max_attempts = 30     # Max number of polling attempts
    poll_interval = 3     # Seconds between each attempt

    for attempt in range(max_attempts):
        response = requests.get(polling_url, headers=headers)
        print(f"[Mindee Vehicle] Polling Attempt {attempt + 1} - Status Code: {response.status_code}")

        if response.status_code == 200:
            status_data = response.json()
            job_status = status_data.get("job", {}).get("status")

            if job_status == "completed":
                # Extract inference data
                data = status_data
                prediction = (
                    data.get("document", {})
                    .get("inference", {})
                    .get("prediction", {})
                )

                # Retrieve vehicle fields
                vin = prediction.get("vehicle_identification_number", {}).get("value", "-")
                license_plate = prediction.get("license_plate_number", {}).get("value", "-")
                make = prediction.get("vehicle_make", {}).get("value", "-")
                model = prediction.get("vehicle_model", {}).get("value", "-")

                return {
                    "vin": vin,
                    "license_plate": license_plate,
                    "make": make,
                    "model": model,
                }

            elif job_status == "failed":
                print("[Mindee Vehicle] Error: Job failed")
                return None

        elif response.status_code == 404:
            print("[Mindee Vehicle] Polling Error: Resource not found")
            return None

        time.sleep(poll_interval)

    print("[Mindee Vehicle] Error: Job did not complete within the maximum attempts")
    return None