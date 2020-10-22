import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="epiphyte", 
    version="0.1.1",
    author="Alana Darcher, Tamara Mueller",
    author_email="alana.darcher@gmail.com",
    description="a Python toolkit for high-dimensional neural data recorded during naturalistic, continuous stimuli",
    long_description="a Python toolkit for high-dimensional neural data recorded during naturalistic, continuous stimuli",
    long_description_content_type="text/markdown",
    url="https://github.com/mackelab/epiphyte",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
