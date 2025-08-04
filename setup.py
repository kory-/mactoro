from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mactoro",
    version="0.1.0",
    author="Shimono",
    author_email="momo0907@gmail.com",
    description="A powerful macOS automation tool for window control and action recording",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kory-/mactoro",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pyobjc",
        "pyautogui>=0.9.54",
        "click>=8.1.7",
        "pillow>=10.0.0",
        "opencv-python>=4.8.0",
        "pynput>=1.7.6",
    ],
    entry_points={
        "console_scripts": [
            "mactoro=mactoro.cli:main",
        ],
    },
)