import setuptools
import os

with open("README.md", "r", encoding="utf-8") as f:
    README = f.read()

with open(os.path.join("requirements", "requirements.txt"), "r") as reqs:
    REQUIREMENTS = reqs.readlines()

with open(os.path.join("requirements", "requirements_test.txt"), "r") as reqs:
    REQUIREMENTS_TEST = reqs.readlines()

setuptools.setup(
    name="pybt",
    version="0.0.2",
    author="Izzudin Hafiz",
    author_email="izzudin.hafiz@gmail.com",
    description="A fast, simple and extensible trade backtesting framework",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/izzudinhafiz/pybt",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha"
    ],
    python_requires=">=3.6",
    install_requires=REQUIREMENTS,
    tests_require=REQUIREMENTS_TEST
)
