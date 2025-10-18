"""
Simple script to test the Face Verification API
"""
import requests
import sys
from pathlib import Path


API_BASE_URL = "http://localhost:8000/api/faceid"


def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_registered_count():
    """Test the registered count endpoint"""
    print("\nTesting registered count endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/registered-count")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        if data.get('success'):
            print(f"✅ Found {data.get('count')} registered face(s)")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_verify(image_path: str):
    """Test face verification with an image"""
    print(f"\nTesting face verification with {image_path}...")
    
    if not Path(image_path).exists():
        print(f"❌ Image file not found: {image_path}")
        return False
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_BASE_URL}/verify", files=files)
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if data.get('success') and data.get('result'):
            result = data['result']
            print(f"\n{'='*50}")
            print(f"Verification Result:")
            print(f"{'='*50}")
            print(f"Verified: {'✅ YES' if result['verified'] else '❌ NO'}")
            print(f"Confidence: {result['confidence']*100:.2f}%")
            
            if result.get('matched_person'):
                print(f"Matched Person: {result['matched_person']}")
            
            print(f"Distance: {result['distance']:.4f}")
            print(f"Threshold: {result['threshold']}")
            print(f"Model: {result['model']}")
            print(f"Detector: {result['detector_backend']}")
            print(f"Metric: {result['similarity_metric']}")
            print(f"{'='*50}\n")
            
            return result['verified']
        else:
            print(f"❌ Verification failed: {data.get('message', 'Unknown error')}")
            if data.get('error'):
                print(f"Error details: {data['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main function"""
    print("="*60)
    print("Face Verification API Test")
    print("="*60)
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed. Make sure the backend is running.")
        return
    
    print("\n✅ Backend is healthy!")
    
    # Test registered count
    if not test_registered_count():
        print("\n⚠️  Could not get registered count")
    
    # Test verification if image path provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_verify(image_path)
    else:
        print("\n" + "="*60)
        print("To test face verification, run:")
        print(f"python {sys.argv[0]} <path_to_image>")
        print("="*60)


if __name__ == "__main__":
    main()

