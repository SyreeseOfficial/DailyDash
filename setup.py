from setuptools import setup, find_packages

setup(
    name="dailydash",
    version="1.0.3",
    packages=find_packages(),
    install_requires=[
        "rich",
        "pygame",
        "psutil",
        "requests",
        "pyperclip",
        "plyer",
    ],
    entry_points={
        "console_scripts": [
            "dailydash=main:main",
        ],
    },
    author="Syreese",
    author_email="syreeseofficial@gmail.com",
    description="Terminal-based Head-Up Display for focus-driven developers",
    url="https://github.com/SyreeseOfficial/DailyDash",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    py_modules=["main"],
)
