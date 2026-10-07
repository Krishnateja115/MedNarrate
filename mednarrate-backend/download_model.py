import requests
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

url = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
dest_dir = "models"
dest_file = os.path.join(dest_dir, "qwen2.5-1.5b-instruct-q4_k_m.gguf")

os.makedirs(dest_dir, exist_ok=True)

session = requests.Session()
retries = Retry(total=20, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

def download_file(url, dest_file):
    headers = {}
    mode = 'wb'
    
    # Check if file exists and get its size
    if os.path.exists(dest_file):
        existing_size = os.path.getsize(dest_file)
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'
        print(f"Resuming download from {existing_size} bytes.")
    else:
        existing_size = 0
        print("Starting new download.")

    while True:
        try:
            with session.get(url, headers=headers, stream=True, timeout=10) as response:
                if response.status_code == 416: # Range not satisfiable, meaning file is fully downloaded
                    print("Download already complete based on server response (416).")
                    return True
                
                response.raise_for_status()
                
                # Check total file size from headers (only on first successful response)
                total_size = int(response.headers.get('content-length', 0))
                if existing_size > 0 and response.status_code == 206: # Partial Content
                    total_size += existing_size
                    
                print(f"Total size: {total_size} bytes")

                with open(dest_file, mode) as f:
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                            existing_size += len(chunk)
                            
            print(f"Download complete. Final size: {existing_size} bytes.")
            return True
            
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            print(f"\nDownload interrupted ({e}). Retrying in 2 seconds...")
            time.sleep(2)
            if os.path.exists(dest_file):
                existing_size = os.path.getsize(dest_file)
                headers['Range'] = f'bytes={existing_size}-'
                mode = 'ab'
                print(f"Resuming download from {existing_size} bytes.")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return False

if __name__ == "__main__":
    download_file(url, dest_file)
