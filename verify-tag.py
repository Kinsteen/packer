import re
import subprocess

pyproject_version_pattern = re.compile(r'version = "(.*)"')

with open("pyproject.toml", "r") as f:
    for line in f.readlines():
        if line.startswith("version = "):
            pyproject_version = re.match(pyproject_version_pattern, line).group(1)

git_tag = subprocess.run("git describe --abbrev=0 --tags".split(), capture_output=True).stdout.decode().strip()

if "v" + pyproject_version != git_tag:
    exit(1)
