import requests
import json
import time

def verify_output():
    print("Reading input data...")
    with open('video_url.json', 'r') as f:
        data = json.load(f)

    url = "http://localhost:8000/generate-plan"
    print(f"Sending request to {url}...")
    
    start_time = time.time()
    try:
        response = requests.post(url, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Received Plan:")
            print(json.dumps(result, indent=2))
            
            # Validate Format
            insertions = result.get('insertions', [])
            if not insertions:
                print("⚠️ No insertions generated. This might be due to LLM logic or video length.")
            else:
                first = insertions[0]
                expected_keys = {"start_sec", "duration_sec", "broll_id", "confidence", "reason"}
                if expected_keys.issubset(first.keys()):
                    print(f"\n✅ Output Format Verified: Contains all required keys {expected_keys}")
                else:
                    print(f"\n❌ Missing Keys. Found: {first.keys()}")
                    
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Is Docker running?")
    except Exception as e:
        print(f"❌ Exception: {e}")
        
    print(f"\nTime taken: {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    verify_output()
