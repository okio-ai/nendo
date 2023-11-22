"""Generate the code reference pages and navigation."""

from pathlib import Path
import re
import os

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()
mod_symbol = '<code class="doc-symbol doc-symbol-nav doc-symbol-module"></code>'
do_not_index = ["utils", "model"]

for path in sorted(Path("src").rglob("*.py")):
    if os.path.splitext(os.path.basename(path))[0] in do_not_index:
        continue
    module_path = path.relative_to("src").with_suffix("")
    doc_path = path.relative_to("src/nendo").with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1].startswith("_"):
        continue

    nav_parts = [f"{mod_symbol} {part}" for part in parts]
    nav[tuple(nav_parts)] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, ".." / path)

pattern = r"\((.*?)\)"
with mkdocs_gen_files.open("reference/SUMMARY.txt", "w") as nav_file:
    for nav_item in nav.build_literate_nav():
        match = re.search(pattern, nav_item)
        if match:
            filepath = match.group(1)
            item = filepath.split("/")[-1].replace(".md", "")
            if item in do_not_index:
                continue
        nav_file.write(nav_item)
