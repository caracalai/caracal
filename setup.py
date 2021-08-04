import setuptools

with open("README.md", 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='pyblocks',
    version='0.0.1',
    long_description=long_description,
    author='BroutonBlocks team',
    classifiers=[
                      "Programming Language :: Python :: 3",
                      "License :: OSI Approved :: MIT License",
                      "Operating System :: OS Independent",
                 ],
    author_email='hello@broutonblocks.com',
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
