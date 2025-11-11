import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

def send_test_sms():
    ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
    ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
    ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
    ZOOM_PHONE_NUMBER = os.getenv("ZOOM_PHONE_NUMBER")
    
    print("🚀 Testing Zoom SMS Endpoints...")
    print(f"From: {ZOOM_PHONE_NUMBER}")
    print(f"To: +12153701259")
    
    # Get OAuth token
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ZOOM_ACCOUNT_ID}"
    auth_string = f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}"
    headers = {
        "Authorization": "Basic " + base64.b64encode(auth_string.encode()).decode()
    }
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("OAuth token obtained")
        else:
            print(f"Token failed: {response.status_code}")
            return
    except Exception as e:
        print(f"💥 Token error: {e}")
        return

    # Try different SMS endpoints
    endpoints = [
        "https://api.zoom.us/v2/phone/messages/sms",
        "https://api.zoom.us/v2/phone/message/sms",
        "https://api.zoom.us/v2/phone/sms_messages",
        "https://api.zoom.us/v2/phone/sms/send",
    ]
    
    sms_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    sms_payload = {
        "to_numbers": ["+12153701259"],
        "from_number": ZOOM_PHONE_NUMBER,
        "message": "Test SMS from MetaSense Recruiter AI - Please ignore this test message. Thank you!"
    }
    
    for endpoint in endpoints:
        print(f"\n🔗 Testing endpoint: {endpoint}")
        try:
            response = requests.post(endpoint, headers=sms_headers, json=sms_payload)
            print(f"📡 Response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("🎉 SUCCESS! SMS endpoint found!")
                print(f"Response: {response.json()}")
                return True
            elif response.status_code == 404:
                print("Endpoint not found")
                continue
            else:
                print(f"Failed: {response.text}")
                # If we get a different error, it might be the right endpoint but with other issues
                if response.status_code != 404:
                    return False
                
        except Exception as e:
            print(f"💥 Error: {e}")
            continue
    
    print("\n🔍 All endpoints failed. Let's discover the correct one...")
    discover_endpoints(token)
    return False

def discover_endpoints(token):
    """Try to discover available phone endpoints"""
    base_url = "https://api.zoom.us/v2"
    endpoints_to_try = [
        "/phone",
        "/phone/numbers", 
        "/phone/users",
        "/phone/messages",
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Discovering available endpoints:")
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(base_url + endpoint, headers=headers)
            print(f"{endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"   Accessible - might contain SMS options")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

if __name__ == "__main__":
    send_test_sms()