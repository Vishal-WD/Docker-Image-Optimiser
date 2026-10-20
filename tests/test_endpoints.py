import io
import requests
from PIL import Image

BASE = "http://127.0.0.1:8000"

def test_all():
    # 1. Health
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    print("1. Health OK:", r.json()["status"])

    # 2. Upload Dockerfile
    dockerfile_content = b"""FROM python:3.11
RUN apt-get update && apt-get install -y gcc build-essential
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
"""
    files = {"file": ("Dockerfile.test", io.BytesIO(dockerfile_content), "text/plain")}
    r2 = requests.post(f"{BASE}/api/upload-dockerfile", files=files)
    assert r2.status_code == 200
    data2 = r2.json()
    print("2. Upload Dockerfile OK:", data2["filename"], "Reduction:", data2["analysis"]["reduction_percentage"], "%")

    # 3. Direct Dockerfile Download (Verify no .txt extension!)
    r_df = requests.post(
        f"{BASE}/api/download/dockerfile",
        json={"dockerfile": data2["optimized_dockerfile"]}
    )
    assert r_df.status_code == 200
    assert 'filename="Dockerfile"' in r_df.headers.get("Content-Disposition", "")
    assert r_df.headers.get("Content-Type") == "application/octet-stream"
    print("3. Direct Dockerfile Download OK: Content-Disposition is", r_df.headers.get("Content-Disposition"))

    # 4. Direct .dockerignore Download (Verify no .txt extension!)
    r_di = requests.post(
        f"{BASE}/api/download/dockerignore",
        json={"dockerfile": data2["optimized_dockerfile"], "dockerignore": data2["dockerignore_content"]}
    )
    assert r_di.status_code == 200
    assert 'filename=".dockerignore"' in r_di.headers.get("Content-Disposition", "")
    print("4. Direct .dockerignore Download OK: Content-Disposition is", r_di.headers.get("Content-Disposition"))

    # 5. Download Docker Bundle (.zip)
    r3 = requests.post(
        f"{BASE}/api/download/docker-bundle",
        json={"dockerfile": data2["optimized_dockerfile"], "dockerignore": data2["dockerignore_content"]}
    )
    assert r3.status_code == 200
    assert len(r3.content) > 100
    print("5. Download Docker Bundle (.zip) OK:", len(r3.content), "bytes")

    # 6. Media upload & direct download
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(10, 80, 200)).save(buf, format="JPEG")
    buf.seek(0)
    r4 = requests.post(
        f"{BASE}/api/optimize-media",
        files={"file": ("sample.jpg", buf, "image/jpeg")},
        data={"quality": 80, "format": "WEBP"}
    )
    assert r4.status_code == 200
    data4 = r4.json()
    print("6. Media Optimize OK, download URL:", data4["download_url"])

    r5 = requests.get(f"{BASE}{data4['download_url']}")
    assert r5.status_code == 200
    assert len(r5.content) > 0
    print("7. Direct Media Download OK:", len(r5.content), "bytes")

    print("\nALL 7 ENDPOINTS VERIFIED & WORKING PERFECTLY!")

if __name__ == "__main__":
    test_all()
