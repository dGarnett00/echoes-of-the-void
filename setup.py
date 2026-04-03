from setuptools import setup, find_packages

setup(
    name="echoes-of-the-void",
    version="0.1.0",
    description="A critically-thinking sci-fi survival text-based game",
    author="dGarnett00",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "colorama>=0.4.6",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "echoes=run:main",
        ],
    },
)
