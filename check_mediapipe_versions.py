import requests
import json

try:
    r = requests.get('https://pypi.org/pypi/mediapipe/json', timeout=10)
    data = r.json()

    versions = ['0.10.14', '0.10.18', '0.10.20', '0.10.21', '0.10.30', '0.10.31', '0.10.32']

    print("MediaPipe Release Dates from PyPI:")
    print("=" * 50)

    for v in versions:
        if v in data['releases']:
            upload_time = data['releases'][v][0]['upload_time'][:10]
            print(f"  {v}: {upload_time}")
        else:
            print(f"  {v}: not found")

    print("\n" + "=" * 50)
    print(f"Latest version: {data['info']['version']}")

except Exception as e:
    print(f"Error fetching data: {e}")
