"""ReadEcho Pro - 智能阅读助手"""

from setuptools import setup, find_packages

setup(
    name="readecho-pro",
    version="1.1.0",
    description="ReadEcho Pro - 智能阅读助手",
    author="ReadEcho Team",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        "PyQt6>=6.4.0",
        "whisper-openai>=20230314",
        "torch>=2.0.0",
        "numpy>=1.24.0",
        "sounddevice>=0.4.6",
        "scipy>=1.10.0",
        "ollama>=0.1.0",
        "requests>=2.28.0",
        "openai>=1.0.0",
        "ebooklib>=0.18",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-qt>=4.2.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "python-dotenv>=1.0.0",
        ],
    },
)
