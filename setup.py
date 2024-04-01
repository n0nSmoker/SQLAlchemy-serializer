from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="SQLAlchemy-serializer",
    version="1.4.12",
    description="Mixin for SQLAlchemy-models serialization without pain",
    long_description_content_type="text/markdown",
    long_description=long_description,
    author="Y-Bro",
    url="https://github.com/n0nSmoker/SQLAlchemy-serializer",
    keywords=["sqlalchemy", "serialize", "to_dict", "JSON"],
    packages=find_packages(exclude=("tests*", "examples*")),
    install_requires=[
        "SQLAlchemy",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
