import os
import sys
import zipfile
import io
import requests

# --- Configuration ---
USERNAME = "anshumanai"
API_TOKEN = os.environ.get("PYTHONANYWHERE_API_TOKEN")
HOST = "www.pythonanywhere.com"
DOMAIN = f"{USERNAME}.pythonanywhere.com"

# Files and folders to exclude from upload
EXCLUDES = {
    ".git",
    ".github",
    ".pytest_cache",
    "__pycache__",
    "venv",
    "spendly.db",
    ".DS_Store",
    ".agents",
    ".coverage",
}


def zip_project():
    """Zips the project files excluding the ones in EXCLUDES."""
    print("Zipping project files...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk("."):
            # Prune excluded directories in place
            dirs[:] = [d for d in dirs if d not in EXCLUDES]

            for file in files:
                if file in EXCLUDES:
                    continue
                file_path = os.path.join(root, file)
                # Archive path relative to project root
                archive_path = os.path.relpath(file_path, ".")
                zip_file.write(file_path, archive_path)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def deploy():
    if not API_TOKEN:
        print("Error: PYTHONANYWHERE_API_TOKEN environment variable not set.")
        sys.exit(1)
    headers = {"Authorization": f"Token {API_TOKEN}"}

    # 1. Zip local directory
    zipped_data = zip_project()

    # 2. Upload zip file to PythonAnywhere
    print("Uploading project to PythonAnywhere...")
    upload_url = (
        f"https://{HOST}/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/project.zip"
    )
    response = requests.post(
        upload_url, headers=headers, files={"content": ("project.zip", zipped_data)}
    )
    if response.status_code not in (200, 201):
        print(f"Failed to upload ZIP: {response.text}")
        return

    # 3. Extract ZIP on PythonAnywhere
    print("Extracting ZIP on PythonAnywhere...")

    # We can write a simple Python script to unzip, upload it, and execute it.
    unzip_script = f"""import zipfile
with zipfile.ZipFile('/home/{USERNAME}/project.zip', 'r') as zip_ref:
    zip_ref.extractall('/home/{USERNAME}/expense-tracker')
"""
    unzip_script_url = (
        f"https://{HOST}/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/unzip.py"
    )
    requests.post(
        unzip_script_url, headers=headers, files={"content": ("unzip.py", unzip_script)}
    )

    # Run the setup script using bash console
    console_url = f"https://{HOST}/api/v0/user/{USERNAME}/consoles/"

    # Clean up existing consoles first to avoid "Console limit reached"
    consoles_res = requests.get(console_url, headers=headers)
    if consoles_res.status_code == 200:
        for c in consoles_res.json():
            print(f"Cleaning up old console {c['id']}...")
            requests.delete(f"{console_url}{c['id']}/", headers=headers)

    print("Creating bash console to extract files and setup virtualenv...")
    create_res = requests.post(
        console_url, headers=headers, json={"executable": "bin/bash"}
    )
    if create_res.status_code == 201:
        console_id = create_res.json()["id"]
        send_url = (
            f"https://{HOST}/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/"
        )

        # Run unzip and setup commands
        setup_cmd = (
            f"echo 'Unzipping files...' && python3 /home/{USERNAME}/unzip.py && "
            f"echo 'Setting up virtualenv...' && cd /home/{USERNAME}/expense-tracker && "
            f"python3 -m venv venv && "
            f"source venv/bin/activate && "
            f"echo 'Installing requirements...' && pip install -r requirements.txt\n"
        )
        requests.post(send_url, headers=headers, json={"input": setup_cmd})
        print("Setup commands sent to console.")
    else:
        print(f"Failed to create setup console: {create_res.text}")
        return

    # 4. Check if Web App exists, otherwise create it
    print("Checking web app configuration...")
    webapps_url = f"https://{HOST}/api/v0/user/{USERNAME}/webapps/"
    webapp_res = requests.get(webapps_url, headers=headers)

    if webapp_res.status_code == 200:
        webapps = [w["domain_name"] for w in webapp_res.json()]
        if DOMAIN not in webapps:
            print(f"Web app {DOMAIN} doesn't exist. Creating web app...")
            create_webapp_res = requests.post(
                webapps_url,
                headers=headers,
                data={"domain_name": DOMAIN, "python_version": "python310"},
            )
            if create_webapp_res.status_code not in (200, 201):
                print(f"Failed to create webapp: {create_webapp_res.text}")
                return

    # 5. Update Web App Settings (Virtualenv path and Source code path)
    webapp_detail_url = f"https://{HOST}/api/v0/user/{USERNAME}/webapps/{DOMAIN}/"
    update_res = requests.patch(
        webapp_detail_url,
        headers=headers,
        json={
            "source_code_path": f"/home/{USERNAME}/expense-tracker",
            "working_directory": f"/home/{USERNAME}/expense-tracker",
            "virtualenv_path": f"/home/{USERNAME}/expense-tracker/venv",
        },
    )
    if update_res.status_code not in (200, 201):
        print(f"Failed to update webapp settings: {update_res.text}")

    # 6. Configure WSGI file on PythonAnywhere
    print("Configuring WSGI file...")
    wsgi_content = f"""import sys
import os

path = '/home/{USERNAME}/expense-tracker'
if path not in sys.path:
    sys.path.append(path)

# Set the environment variable for your Flask app's secret key (change this to something secure)
os.environ['SECRET_KEY'] = 'dev-secret-key-pythonanywhere'

from app import app as application
"""
    wsgi_url = f'https://{HOST}/api/v0/user/{USERNAME}/files/path/var/www/{USERNAME.replace(".", "_")}_pythonanywhere_com_wsgi.py'
    wsgi_res = requests.post(
        wsgi_url, headers=headers, files={"content": ("wsgi.py", wsgi_content)}
    )
    if wsgi_res.status_code not in (200, 201):
        print(f"Warning: Failed to write WSGI file: {wsgi_res.text}")

    # 7. Reload Web App
    print("Reloading web app to apply changes...")
    reload_url = f"https://{HOST}/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    reload_res = requests.post(reload_url, headers=headers)
    if reload_res.status_code == 200:
        print(f"\n🎉 Successfully deployed! Your site is live at: http://{DOMAIN}")
    else:
        print(f"Failed to reload webapp: {reload_res.text}")


if __name__ == "__main__":
    # Make sure requests is installed locally
    try:
        import requests
    except ImportError:
        print("Please install the 'requests' library: pip install requests")
        sys.exit(1)

    deploy()
