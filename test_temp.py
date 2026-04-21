import requests

BASE_URL = "http://127.0.0.1:8000"

def get_token(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    return resp.json()["access_token"]

def test_batch_summary():
    token = get_token("abc@college.com", "Test@1234")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/batches/5/summary", headers=headers)
    print("\n--- Batch Summary ---")
    print(f"Status: {resp.status_code}")
    print(resp.json())

def test_institution_summary():
    token = get_token("manager@skillbridge.com", "Test@1234")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/institutions/13/summary", headers=headers)
    print("\n--- Institution Summary ---")
    print(f"Status: {resp.status_code}")
    print(resp.json())

def test_programme_summary():
    token = get_token("manager@skillbridge.com", "Test@1234")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/programme/summary", headers=headers)
    print("\n--- Programme Summary ---")
    print(f"Status: {resp.status_code}")
    print(resp.json())

if __name__ == "__main__":
    test_batch_summary()
    test_institution_summary()
    test_programme_summary()