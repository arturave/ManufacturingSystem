"""
Setup script for Manufacturing System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="manufacturing-system",
    version="1.1.0",
    author="Production IT Team",
    author_email="support@production.local",
    description="System Zarządzania Produkcją - Laser/Prasa Krawędziowa",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://production.local",
    project_urls={
        "Bug Tracker": "https://github.com/production/manufacturing-system/issues",
        "Documentation": "https://production.local/docs",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: Other/Proprietary License",
        "Natural Language :: Polish",
        "Topic :: Office/Business",
        "Topic :: Office/Business :: Scheduling",
        "Framework :: CustomTkinter",
    ],
    python_requires=">=3.11",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    include_package_data=True,
    package_data={
        "": ["*.sql", "*.md", "*.txt", "*.bat", ".env.example"],
    },
    install_requires=[
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        "supabase>=2.3.0",
        "tkcalendar>=1.6.1",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "python-docx>=1.1.0",
        "reportlab>=4.0.0",
        "matplotlib>=3.7.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "outlook": ["pywin32>=305"],
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "pylint>=2.17.0",
            "mypy>=1.4.0",
            "flake8>=6.0.0",
        ],
        "build": [
            "wheel>=0.40.0",
            "twine>=4.0.0",
            "build>=0.10.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "mfg-system=mfg_integrated:main",
        ],
        "gui_scripts": [
            "mfg-system-gui=mfg_integrated:main",
        ],
    },
    zip_safe=False,
)
