import requests
import time

language_codes = {
    'python': 71,
    'javascript': 93,
    'c++': 54,
    'c': 50,
    'java': 62
}


def test_code(source_code, inpt, output, language):
    url = "https://judge0-ce.p.rapidapi.com/submissions"
    submit_query = {"base64_encoded": "false", "wait": "false", "fields": "*"}

    payload = {
        "language_id": language_codes[language],
        "source_code": source_code,
        "stdin": f'{inpt}\n' if inpt else ''
    }

    headers = {
        "x-rapidapi-key": "0ebffb008bmshf808d7e44b43492p16da87jsn49a253c20c43",
        "x-rapidapi-host": "judge0-ce.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    # Step 1: Submit code
    submit_response = requests.post(url, json=payload, headers=headers, params=submit_query)
    token = submit_response.json()["token"]

    # === Poll for result ===
    get_url = f"https://judge0-ce.p.rapidapi.com/submissions/{token}"
    get_query = {"base64_encoded": "false", "fields": "*"}

    # Wait a moment before fetching result
    time.sleep(2)

    # Step 2: Get result
    result_response = requests.get(get_url, headers=headers, params=get_query)
    result_data = result_response.json()

    # Step 3: Check results
    if result_data.get("stderr"):
        return result_data.get("stderr")
    else:
        return result_data.get("stdout") == f'{output}\n'
