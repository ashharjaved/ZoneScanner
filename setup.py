from setuptools import setup, find_packages

setup(
    name="ZoneScanner",
    version="0.1.0",
    description="Multi-timeframe demand zone detector with plotting",
    author="Ashhar Javed",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'plotly',
        'yfinance',
        'requests',
        'stockfetcher'
    ],
    entry_points={
        'console_scripts': [
            'demandzone=ZoneScanner.main:main',
            'fetch-stocks=ZoneScanner.fetch:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)