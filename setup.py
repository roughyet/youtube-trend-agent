import sys
from setuptools import setup

# Force Python 3.11 check
if sys.version_info >= (3, 14):
    print("ERROR: Python 3.14+ is not supported. Use Python 3.11")
    sys.exit(1)

setup(
    name="youtube-trend-agent",
    version="1.0.0",
    python_requires=">=3.11,<3.12",
    install_requires=[
        "python-telegram-bot==21.1",
        "google-generativeai==0.3.0",
        "requests==2.31.0",
        "protobuf==4.25.3",
    ],
)
