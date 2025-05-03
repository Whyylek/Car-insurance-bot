import requests
import json
import time

def extract_passport_data(image_bytes, api_key):
    url = "https://api.mindee.net/v1/products/mindee/passport/v1/predict"
    headers = {"Authorization": f"Token {api_key}"}
    files = {"document": image_bytes}

    if not api_key:
        print("[Mindee] Error: API Key is missing")
        return None

    try:
        response = requests.post(url, headers=headers, files=files)
        print(f"[Mindee] Status Code: {response.status_code}")
       

        if response.status_code == 201:
            data = response.json()
            prediction = (
                data.get("document", {})
                .get("inference", {})
                .get("prediction", {})
            )

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

        # Extract job ID and polling URL
        job_data = response.json()
        job_id = job_data.get("job", {}).get("id")
        polling_url = job_data.get("job", {}).get("polling_url")
        if not job_id or not polling_url:
            print("[Mindee Vehicle] Error: No job ID or polling URL returned")
            return None

        # Poll for the result using the provided polling URL
        return poll_for_vehicle_result(polling_url, api_key)

    except Exception as e:
        print(f"[Mindee Vehicle] Network/Error: {e}")
        return None

def poll_for_vehicle_result(polling_url, api_key):
    headers = {"Authorization": f"Token {api_key}"}

    max_attempts = 30  # 30 attempts = 90 seconds with 3-second intervals
    poll_interval = 3  # Seconds between polling attempts

    for attempt in range(max_attempts):
        response = requests.get(polling_url, headers=headers)
        print(f"[Mindee Vehicle] Polling Attempt {attempt + 1} - Status Code: {response.status_code}")
       

        if response.status_code == 200:
            status_data = response.json()
            job_status = status_data.get("job", {}).get("status")

            if job_status == "completed":
                # The polling response contains the document data directly
                data = status_data
                prediction = (
                    data.get("document", {})
                    .get("inference", {})
                    .get("prediction", {})
                )

                # Extract fields with correct names
                vin = prediction.get("vehicle_identification_number", {}).get("value", "-")
                license_plate = prediction.get("license_plate_number", {}).get("value", "-")

                return {
                    "vin": vin,
                    "license_plate": license_plate
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