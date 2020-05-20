import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DeepHumanVision-Mackelab", 
    version="0.0.1",
    author="Alana Darcher, Tamara Mueller",
    author_email="tamara.mueller@tum.de",
    description="Processing pipeline for single-unit neural activity",
    long_description="Processing pipeline for high-dimensional single-unit neural activity colligated with meta data",
    long_description_content_type="text/markdown",
    url="https://github.com/mackelab/DeepHumanVision_deploy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
