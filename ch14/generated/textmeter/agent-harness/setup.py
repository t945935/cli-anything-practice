"""Install the book's generated TextMeter harness."""
from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-textmeter",
    version="0.1.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    python_requires=">=3.10",
    install_requires=[
        "cli-anything-practice-textmeter-core==0.1.0",
        "click>=8.1,<9",
        "prompt-toolkit>=3.0,<4",
    ],
    package_data={"cli_anything.textmeter": ["skills/*.md", "README.md"]},
    entry_points={"console_scripts": [
        "cli-anything-textmeter=cli_anything.textmeter.textmeter_cli:main"
    ]},
)
