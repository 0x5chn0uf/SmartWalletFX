from setuptools import find_packages, setup

setup(
    name="smartwalletfx",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.115.12",
        "uvicorn==0.34.3",
        "python-dotenv==1.1.0",
        "requests==2.32.3",
        "aiohttp==3.12.9",
        "sqlalchemy==2.0.41",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-multipart==0.0.9",
    ],
)
