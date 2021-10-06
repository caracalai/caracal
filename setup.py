import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="broutonblocks",
    version="0.0.1",
    long_description=long_description,
    author="BroutonLab team",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    author_email="hello@broutonblocks.com",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=[
        "pycodestyle==2.6.0",
        "black==21.4b2",
        "flake8==3.8.3",
        "flake8-bugbear==20.1.4",
        "flake8-builtins==1.5.3",
        "flake8-comprehensions==3.2.3",
        "flake8-docstrings==1.5.0",
        "flake8-import-order==0.18.1",
        "flake8-tidy-imports==4.1.0",
    ],
    python_requires=">=3.6",
)
