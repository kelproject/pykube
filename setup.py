from setuptools import setup, find_packages


with open("README.rst") as fp:
    long_description = fp.read()


setup(
    name="pykube",
    version="0.5.1",
    description="Python client library for Kubernetes",
    long_description=long_description,
    author="Eldarion, Inc.",
    author_email="development@eldarion.com",
    license="Apache",
    url="https://github.com/eldarion-gondor/pykube",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    zip_safe=False,
    packages=find_packages(),
    install_requires=[
        "requests",
        "PyYAML",
    ],
)
