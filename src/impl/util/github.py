import warnings
warnings.filterwarnings('ignore', message='Unable to find acceptable character detection')
import requests
import os


def gen_github_api_link(owner, repo, branch="main", path=""):
    """
    Generate a GitHub API URL to get the contents of a repository, branch, or folder.

    Parameters:
        owner (str): GitHub username or organization.
        repo (str): Repository name.
        branch (str): Branch name (default: 'main').
        path (str): Path inside the repo (folder or file, default: root).

    Returns:
        str: GitHub API URL to access the contents.
    """
    path = path.strip("/")  # remove leading/trailing slashes
    if path:
        url = (
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        )
    else:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/?ref={branch}"
    return url


def list_github_contents(owner=None, repo=None, branch="main", path="", api_url=None):
    """
    List the contents (files and folders) of a GitHub repo/folder.

    Can either provide owner/repo/branch/path or a full api_url.

    Returns:
        List of dicts with 'name' and 'type' keys.
    """
    url = api_url or gen_github_api_link(owner, repo, branch, path)
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    contents = [{"name": item["name"], "type": item["type"]} for item in data]
    return contents


def download_github_folder(
    owner=None, repo=None, branch="main", path="", local_dir="", api_url=None
):
    """
    Download a folder from a GitHub repo recursively.

    Can either provide owner/repo/branch/path or a full api_url.
    """
    url = api_url or gen_github_api_link(owner, repo, branch, path)
    response = requests.get(url)
    response.raise_for_status()
    items = response.json()

    if not local_dir:
        local_dir = path or "root"
    os.makedirs(local_dir, exist_ok=True)

    for item in items:
        item_name = item["name"]
        item_type = item["type"]
        item_path = os.path.join(local_dir, item_name)

        if item_type == "dir":
            sub_api_url = item.get("url")  # GitHub API url for subfolder
            download_github_folder(api_url=sub_api_url, local_dir=item_path)
        elif item_type == "file":
            file_url = item["download_url"]
            file_data = requests.get(file_url).content
            with open(item_path, "wb") as f:
                f.write(file_data)
            print(f"Downloaded {item_path}")


def download_github_file(
    owner=None, repo=None, branch="main", file_path="", local_file="", api_url=None
):
    """
    Download a single file from GitHub.

    Can either provide owner/repo/branch/file_path or a full api_url.
    """
    url = api_url or gen_github_api_link(owner, repo, branch, file_path)
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if data["type"] != "file":
        raise ValueError(f"{file_path} is not a file.")

    file_data = requests.get(data["download_url"]).content
    if not local_file:
        local_file = os.path.basename(file_path)
    os.makedirs(os.path.dirname(local_file) or ".", exist_ok=True)
    with open(local_file, "wb") as f:
        f.write(file_data)
    print(f"Downloaded {local_file}")


if __name__ == "__main__":
    owner = "Delici0u-s"
    repo = "Amca"
    branch = "rewrite"
    folder = "preset_plugins"

    print("Listing contents:")
    contents = list_github_contents(owner, repo, branch, folder)
    for item in contents:
        print(item)

    # Example: download a folder recursively
    download_github_folder(owner, repo, branch, folder, "local_preset_plugins")

    # Example: download a single file
    # download_github_file(owner, repo, branch, "preset_plugins/somefile.py", "somefile.py")

    # Example: using a full API path
    api_url = "https://api.github.com/repos/Delici0u-s/Amca/contents/preset_plugins?ref=rewrite"
    download_github_folder(api_url=api_url, local_dir="local_preset_plugins_api_url")
