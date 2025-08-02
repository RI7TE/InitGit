import setuptools


setuptools.setup(
    name="initgit",
    version="0.1.0",
    author="Steven Kellum",
    author_email="sk@perfectatrifecta.com",
    description="InitGit is a Python package that provides a set of tools for initializing and managing Git repositories.",
    download_url="https://github.com/RI7TE/InitGit.git",
    py_modules=["initgit", "_license", "__main__"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.10",
    requires=["colorama==0.4.6"],
)
