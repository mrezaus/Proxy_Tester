import requests
import concurrent.futures
import re
import urllib3
import time
import json

# Disable SSL-related warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TEST_URL = "https://www.google.com/generate_204"
TIMEOUT = 5

def leech_proxies_from_url(url):
    """Extract proxies from a website (supports both raw HTML and JSON files)"""
    print(f"[*] Fetching proxies from {url} ...")
    
    # Add a browser User-Agent header so the site doesn't block us as a bot
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        proxies = set()
        
        # Case 1: Check if the URL points directly to a JSON file (e.g., API database)
        try:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Find common keys used for IP and Port
                        host = item.get('host') or item.get('ip')
                        port = item.get('port')
                        if host and port:
                            proxies.add(f"{host}:{port}")
            if proxies:
                return list(proxies)
        except json.JSONDecodeError:
            # If the output is not JSON, it's fine; proceed to Case 2
            pass
            
        # Case 2: Extract proxies using Regular Expressions (Regex) for plain text websites
        found_proxies = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b', response.text)
        proxies.update(found_proxies)
        
        return list(proxies)
    except Exception as e:
        print(f"[-] Error fetching from URL: {e}")
        return []

def load_proxies_from_file(filepath):
    print(f"[*] Reading proxies from {filepath} ...")
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            proxies = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b', content)
            return list(set(proxies))
    except Exception as e:
        print(f"[-] Error reading file: {e}")
        return []

def check_proxy(proxy):
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }
    try:
        # Send a test request to the TEST_URL
        response = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT, verify=False)
        
        # Accept both 200 (OK) and 204 (No Content) for endpoints like google.com/generate_204
        if response.status_code in [200, 204]:
            print(f"[+] VALID: {proxy}")
            return proxy
    except Exception:
        pass
    return None

def main():
    print("=== Advanced Proxy Leecher & Checker ===")
    print("1. Leech proxies from a Website URL or API (JSON)")
    print("2. Load proxies from a Local Text File")
    
    choice = input("Select an option (1 or 2): ").strip()
    
    proxy_list = []
    
    if choice == '1':
        url = input("Enter the URL (e.g., https://.../proxies.json): ").strip()
        proxy_list = leech_proxies_from_url(url)
    elif choice == '2':
        filepath = input("Enter the path to the text file (e.g., proxies.txt): ").strip()
        proxy_list = load_proxies_from_file(filepath)
    else:
        print("[-] Invalid choice. Exiting.")
        return

    if not proxy_list:
        print("[-] No proxies found. The site might be using JS rendering or Cloudflare protection.")
        return

    print(f"[*] Total unique proxies found: {len(proxy_list)}")
    
    try:
        threads = int(input("Enter the number of threads (e.g., 20, 50): ").strip())
    except ValueError:
        print("[-] Invalid number. Defaulting to 20 threads.")
        threads = 20

    print(f"[*] Starting test with {threads} threads...\n")
    
    working_proxies = []
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(check_proxy, p): p for p in proxy_list}
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                working_proxies.append(result)

    end_time = time.time()
    
    print("\n=== Summary ===")
    print(f"[*] Tested: {len(proxy_list)} proxies")
    print(f"[*] Working: {len(working_proxies)} proxies")
    print(f"[*] Time Taken: {round(end_time - start_time, 2)} seconds")

    if working_proxies:
        with open("working_proxies.txt", "w") as f:
            for wp in working_proxies:
                f.write(wp + "\n")
        print("[+] Working proxies have been saved to 'working_proxies.txt'")

if __name__ == "__main__":
    main()