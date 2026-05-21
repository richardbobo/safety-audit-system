import requests
import time

def check_service(url, name, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, f"{name}: UP (Status: {response.status_code})"
        else:
            return False, f"{name}: DOWN (Status: {response.status_code})"
    except requests.exceptions.ConnectionError:
        return False, f"{name}: DOWN (Connection failed)"
    except Exception as e:
        return False, f"{name}: ERROR ({str(e)})"

def main():
    print("Checking Safety Audit System Services...")
    print("=" * 50)
    
    services = [
        ("http://localhost:8000/health", "Main Backend (8000)"),
        ("http://localhost:8002/health", "AI Audit (8002)"),
        ("http://localhost:8000/static/dashboard.html", "Dashboard Page"),
        ("http://localhost:8000/docs", "API Documentation")
    ]
    
    all_up = True
    for url, name in services:
        is_up, message = check_service(url, name)
        print(f"[OK] {message}" if is_up else f"[FAIL] {message}")
        if not is_up:
            all_up = False
        time.sleep(0.5)
    
    print("=" * 50)
    if all_up:
        print("[SUCCESS] All services are running!")
        print("\nAccess URLs:")
        print("1. Dashboard: http://localhost:8000/static/dashboard.html")
        print("2. SOP Management: http://localhost:8000/static/sops.html")
        print("3. Standards: http://localhost:8000/static/standards.html")
        print("4. API Docs: http://localhost:8000/docs")
        print("5. AI Service: http://localhost:8002")
        print("\nDefault login: admin / admin123")
    else:
        print("[WARNING] Some services are not responding")

if __name__ == "__main__":
    main()