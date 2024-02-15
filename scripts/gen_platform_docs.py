"""Generate the documentation for the Nendo Platform."""

import os
import shutil

from git import Repo

banner_image_code = [
    "<br>\n",
    '<p align="left">\n',
    '    <img src="https://okio.ai/docs/assets/nendo_logo.png" width="500" alt="Nendo Core">\n',
    "</p>\n",
    "<br>\n",
]

# Local directory to store the plugin documentation
local_dir = "./platformdocs"

# Reset local directory
shutil.rmtree(local_dir, ignore_errors=True)
os.makedirs(local_dir, exist_ok=True)


def remove_block_of_lines(file_path, block):
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Convert the block into a single string for easy comparison
    block_str = "".join(block)

    # Join the lines in the file for comparison
    file_str = "".join(lines)

    # Remove the block if it exists
    file_str = file_str.replace(block_str, "")

    # Write back the modified content
    with open(file_path, "w") as file:
        file.write(file_str)


print(f"Generating docs for nendo_platform...")
# Clone the repos into a temporary directory
repo_path = os.path.join(local_dir)
os.makedirs(repo_path, exist_ok=True)
temp_dir_platform = os.path.join("/tmp", "nendo_platform")
temp_dir_server = os.path.join("/tmp", "nendo_server")
temp_dir_web = os.path.join("/tmp", "nendo_web")
shutil.rmtree(temp_dir_platform, ignore_errors=True)
shutil.rmtree(temp_dir_server, ignore_errors=True)
shutil.rmtree(temp_dir_web, ignore_errors=True)
Repo.clone_from("git@github.com:okio-ai/nendo_devops.git", temp_dir_platform)
Repo.clone_from("git@github.com:okio-ai/nendo_server.git", temp_dir_server)
Repo.clone_from("git@github.com:okio-ai/nendo_web.git", temp_dir_web)

# copy README files to platformdocs
platform_file_path = os.path.join(repo_path, "platform.md")
server_file_path = os.path.join(repo_path, "server.md")
web_file_path = os.path.join(repo_path, "web.md")
shutil.copy2(os.path.join(temp_dir_platform, "README.md"), platform_file_path)
shutil.copy2(os.path.join(temp_dir_server, "README.md"), server_file_path)
shutil.copy2(os.path.join(temp_dir_web, "README.md"), web_file_path)
remove_block_of_lines(platform_file_path, banner_image_code)
remove_block_of_lines(server_file_path, banner_image_code)
remove_block_of_lines(web_file_path, banner_image_code)
shutil.rmtree(temp_dir_platform)
shutil.rmtree(temp_dir_server)
shutil.rmtree(temp_dir_web)
