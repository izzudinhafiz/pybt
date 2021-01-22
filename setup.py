import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="pybt_mihizzudin",
    version="0.0.1",
    author="Izzudin Hafiz",
    author_email="izzudin.hafiz@gmail.com",
    description="A fast, simple and extensible trade backtesting framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/izzudinhafiz/pybt",
    packages=setuptools.find_packages(),
    classifiers=[
        "Progamming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha"
    ],
    python_requires=">=3.6"
)
