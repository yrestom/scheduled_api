from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in scheduled_api/__init__.py
from scheduled_api import __version__ as version

setup(
    name="scheduled_api",
    version=version,
    description="Scheduled API",
    author="Totrox & Aakvatech",
    author_email="info@totrox.cmo & info@aakvatech.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
