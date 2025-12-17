from setuptools import setup, find_packages

setup(
    name="masteratpdf",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyMuPDF>=1.23.22",
        "python-docx>=1.1.0",
        "lxml>=4.9.3",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "masteratpdf=masteratpdf.cli:main",
        ]
    },
)