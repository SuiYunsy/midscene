"""
Midscene Python SDK 安装脚本
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mspy",
    version="0.1.0",
    author="Midscene Team",
    author_email="",
    description="AI驱动的UI自动化测试SDK (Python版本)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/web-infra-dev/midscene",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "pyyaml>=6.0",
        "openai>=1.0.0",
        "pillow>=10.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mspy=mspy.cli.main:main",
        ],
    },
    keywords="testing, automation, ai, ui-testing, playwright",
    project_urls={
        "Bug Reports": "https://github.com/web-infra-dev/midscene/issues",
        "Source": "https://github.com/web-infra-dev/midscene",
        "Documentation": "https://midscenejs.com",
    },
)
