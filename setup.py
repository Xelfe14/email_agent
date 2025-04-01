from setuptools import setup, find_packages

setup(
    name="email_agent",
    version="0.1.0",
    packages=find_packages(),
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered email response generation system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/email_agent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
