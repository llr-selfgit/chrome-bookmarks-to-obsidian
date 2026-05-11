from setuptools import find_packages, setup


setup(
    name="chrome-bookmarks-to-obsidian",
    version="0.1.0",
    description="Import a Chrome bookmark folder into a structured Obsidian web knowledge base.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="llr-selfgit",
    python_requires=">=3.9",
    packages=find_packages(include=["chrome_bookmarks_to_obsidian*"]),
    entry_points={
        "console_scripts": [
            "chrome-bookmarks-to-obsidian=chrome_bookmarks_to_obsidian.cli:main",
        ]
    },
)
