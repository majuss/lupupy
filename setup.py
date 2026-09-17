"""LupuPy setup script."""

from setuptools import find_packages, setup

PACKAGES = find_packages()

setup(
    name="lupupy",
    version="0.3.3-dev-1",
    description="",
    author="majuss",
    url="http://www.github.com/majuss/lupupy",
    platforms="any",
    packages=PACKAGES,
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=["requests>=2.12.4", "pyyaml", "colorlog"],
    test_suite="tests",
    entry_points={"console_scripts": ["lupupy = lupupy.__main__:main"]},
)
