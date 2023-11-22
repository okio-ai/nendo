"""Generate the documentation for the plugins."""

import os
import sys
import shutil
from git import Repo
from urllib.parse import urlparse

# List of GitHub repository URLs
github_repos = [
    "https://github.com/okio-ai/nendo_plugin_stemify_demucs/",
    "https://github.com/okio-ai/nendo_plugin_classify_core/",
    "https://github.com/okio-ai/nendo_plugin_quantize_core/",
    "https://github.com/okio-ai/nendo_plugin_fx_core/",
    "https://github.com/okio-ai/nendo_plugin_loopify/",
    "https://github.com/okio-ai/nendo_plugin_musicgen/",
    "https://github.com/okio-ai/nendo_plugin_vampnet/",
    # "https://github.com/okio-ai/nendo_plugin_library_postgres/",
]

banner_image_code = [
    "<br>\n",
    '<p align="left">\n',
    '    <img src="https://okio.ai/docs/assets/nendo_core_logo.png" width="350" alt="nendo core">\n',
    "</p>\n",
    "<br>\n",
]

# Local directory to store the plugin documentation
local_dir = "./plugindocs"

# Ensure local_dir exists
shutil.rmtree(local_dir, ignore_errors=True)
os.makedirs(local_dir, exist_ok=True)


def process_name(name):
    # Removing the 'nendo_plugin_' prefix
    if name.startswith("nendo_plugin_"):
        name = name[len("nendo_plugin_") :]

    # Replacing underscores with whitespaces and capitalizing each word
    return " ".join(word.capitalize() for word in name.split("_"))


def replace_string_in_file(file_path, target_string, replacement_string):
    # Read the contents of the file
    with open(file_path, "r", encoding="utf-8") as file:
        file_contents = file.read()

    # Replace the target string with the replacement string
    file_contents = file_contents.replace(target_string, replacement_string)

    # Write the updated contents back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(file_contents)


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


def copy_or_create_docs(repo_url, repo_name):
    """Copy the docs folder and other files, or create them if not present."""
    repo_path = os.path.join(local_dir, repo_name)
    os.makedirs(repo_path, exist_ok=True)
    # Clone the repo to a temporary directory
    temp_dir = os.path.join("/tmp", repo_name)
    shutil.rmtree(temp_dir, ignore_errors=True)
    Repo.clone_from(repo_url, temp_dir)

    print(f"Generating docs for {repo_name}...")

    if os.path.exists(os.path.join(temp_dir, "docs/")):
        # Copy the docs folder and specified files
        shutil.copytree(
            os.path.join(temp_dir, "docs"),
            os.path.join(repo_path, "docs"),
            dirs_exist_ok=True,
        )
        for file in ["README.md", "mkdocs.yml", "contributing.md"]:
            if os.path.exists(os.path.join(temp_dir, file)):
                shutil.copy2(os.path.join(temp_dir, file), repo_path)

        for root, dirs, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                replace_string_in_file(
                    file_path, '--8<-- "', f'--8<-- "plugindocs/{repo_name}/'
                )
                replace_string_in_file(file_path, "](docs/", "](")
                remove_block_of_lines(file_path, banner_image_code)

        # Clean up the cloned repository
        shutil.rmtree(temp_dir)
    else:
        # Create docs/ and index.md
        os.makedirs(os.path.join(repo_path, "docs"), exist_ok=True)
        shutil.copy2(
            os.path.join("/tmp", repo_name, "README.md"),
            os.path.join(repo_path, "docs", "index.md"),
        )
        processed_repo_name = process_name(repo_name)

        # Create mkdocs.yml
        with open(os.path.join(repo_path, "mkdocs.yml"), "w") as mkdocs_file:
            mkdocs_file.write(
                f'site_name: {processed_repo_name}\n\nnav:\n  - {processed_repo_name}: "index.md"'
            )


for repo_url in github_repos:
    parsed_url = urlparse(repo_url)
    repo_name = parsed_url.path.split("/")[-2]
    copy_or_create_docs(repo_url, repo_name)
