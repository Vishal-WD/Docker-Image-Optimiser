import io
import json
import tarfile
import urllib.request
import zipfile

base_url = "http://127.0.0.1:8000"

print("=" * 80)
print(" STEP 1: UPLOADING BLOATED DOCKERFILE TO /api/upload-dockerfile")
print("=" * 80)

with open("Dockerfile.unoptimized", "rb") as f:
    df_bytes = f.read()

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = io.BytesIO()
body.write(f"--{boundary}\r\n".encode())
body.write(b'Content-Disposition: form-data; name="file"; filename="Dockerfile.unoptimized"\r\n')
body.write(b"Content-Type: text/plain\r\n\r\n")
body.write(df_bytes)
body.write(b"\r\n")
body.write(f"--{boundary}\r\n".encode())
body.write(b'Content-Disposition: form-data; name="project_name"\r\n\r\n')
body.write(b"my-bloated-python-service\r\n")
body.write(f"--{boundary}--\r\n".encode())

req_upload = urllib.request.Request(
    f"{base_url}/api/upload-dockerfile",
    data=body.getvalue(),
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)

with urllib.request.urlopen(req_upload) as res:
    upload_res = json.loads(res.read().decode("utf-8"))

print(f"Uploaded File     : {upload_res['filename']} ({upload_res['file_size_kb']} KB)")
print(f"Original Footprint: {upload_res['analysis']['estimated_original_mb']} MB")
print(f"Optimized Footprint: {upload_res['analysis']['estimated_optimized_mb']} MB")
print(f"Footprint Saving  : -{upload_res['analysis']['reduction_percentage']}% (Saved {upload_res['analysis']['saved_mb']} MB)")
print(f"Issues Detected   : {upload_res['analysis']['issue_count']} bloat anti-patterns")
print(f"Database Record   : ID #{upload_res['id']}")

print("\n" + "=" * 80)
print(" STEP 2: DOWNLOADING THE 3 KEPT ARTIFACTS (.tar, .txt, .zip)")
print("=" * 80)

opt_df = upload_res["optimized_dockerfile"]
opt_di = upload_res["dockerignore_content"]
di_payload = json.dumps({"dockerfile": opt_df, "dockerignore": opt_di}).encode("utf-8")

# Download 1: Docker Image TAR
req_tar = urllib.request.Request(f"{base_url}/api/download/docker-image-tar", data=b"", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req_tar) as res:
    tar_bytes = res.read()
    tar_cd = res.headers.get("Content-Disposition")
    tar_ct = res.headers.get("Content-Type")

# Download 2: dockerignore.txt
req_di = urllib.request.Request(f"{base_url}/api/download/dockerignore", data=di_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req_di) as res:
    di_bytes = res.read()
    di_cd = res.headers.get("Content-Disposition")
    di_ct = res.headers.get("Content-Type")

# Download 3: Docker Bundle ZIP
req_zip = urllib.request.Request(f"{base_url}/api/download/docker-bundle", data=di_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req_zip) as res:
    zip_bytes = res.read()
    zip_cd = res.headers.get("Content-Disposition")
    zip_ct = res.headers.get("Content-Type")

print(f"1. Docker Image (.tar) : {len(tar_bytes):,} bytes | MIME: {tar_ct} | Filename: {tar_cd}")
print(f"2. dockerignore.txt    : {len(di_bytes):,} bytes | MIME: {di_ct} | Filename: {di_cd}")
print(f"3. Bundle (.zip)       : {len(zip_bytes):,} bytes | MIME: {zip_ct} | Filename: {zip_cd}")

print("\n" + "=" * 80)
print(" STEP 3: COMPARISON OF FORMATS, PURPOSES & INTERNAL CONTENTS")
print("=" * 80)

# Compare 1: Docker Image TAR (.tar)
tf = tarfile.open(fileobj=io.BytesIO(tar_bytes))
tar_members = tf.getnames()
print("\n[1] DOCKER IMAGE TAR ARCHIVE (.tar)")
print("    - Intended For : Direct container engine deployment (`docker load -i image-optimizer-optimized.tar`)")
print("    - Format Spec  : Official Docker Image Specification (v1.2)")
print(f"    - Total Entries: {len(tar_members)} files/directories")
print("    - Key Contents :")
for m in tar_members:
    print(f"        * {m}")

# Compare 2: dockerignore.txt
print("\n[2] DOCKERIGNORE (.txt)")
print("    - Intended For : Build context size reduction (prevents uploading .git, tests, node_modules to daemon)")
print("    - Format Spec  : Standard UTF-8 plain text file with pattern matching rules")
print(f"    - Total Size   : {len(di_bytes)} bytes")
print("    - Sample Rules :")
for r in di_bytes.decode("utf-8").splitlines()[:6]:
    if r.strip():
        print(f"        * {r}")
print("        * ...")

# Compare 3: Docker Bundle (.zip)
zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
zip_members = zf.namelist()
print("\n[3] DOCKER BUNDLE (.zip)")
print("    - Intended For : Complete project portability & source distribution")
print("    - Format Spec  : Standard ZIP archive (openable natively in Windows / macOS / Linux)")
print(f"    - Total Files  : {len(zip_members)}")
print("    - Packaged Files:")
for zm in zip_members:
    print(f"        * {zm} ({zf.getinfo(zm).file_size} bytes)")

print("\n" + "=" * 80)
print(" WORKFLOW COMPLETE & VERIFIED!")
print("=" * 80)
