from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="lavanya_service",
    version="1.0.0",
    description="Lavanya Service Platform — Complaint management, brand follow-up, WhatsApp bot",
    author="Lavanya eMart",
    author_email="tech@lavanyaemart.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
