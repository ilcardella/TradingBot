from setuptools import setup, find_namespace_packages
import os

setup(
    name="TradingBot",
    version="1.1.0",
    python_requires='>=3',

    package_dir={'': 'src'},
    packages=find_namespace_packages(where='src'),
    scripts=['src/TradingBot.py'],
    entry_points={
        'console_scripts': [
            'trading_bot = TradingBot:main'
        ],
    },

    install_requires=[
        'alpha-vantage==2.1.2',
        'certifi==2019.11.28',
        'chardet==3.0.4',
        'govuk-bank-holidays==0.5',
        'idna==2.8',
        'numpy==1.17.4',
        'panda==0.3.1',
        'pandas==0.25.2',
        'python-dateutil==2.8.1',
        'pytz==2019.3',
        'requests==2.22.0',
        'scipy==1.4.1',
        'six==1.13.0',
        'urllib3==1.25.7',
    ],

    package_data={
        'config': ['*.json']
    },
    data_files=[
        (os.path.join(os.path.expanduser('~'), '.TradingBot', 'config'), ['config/config.json'])
    ],

    # metadata to display on PyPI
    author="Alberto Cardellini",
    author_email="",
    description="Autonomous market trading script",
    keywords="trading stocks finance",
    url="https://github.com/ilcardella/TradingBot",
    project_urls={
        "Bug Tracker": "https://github.com/ilcardella/TradingBot/issues",
        "Documentation": "https://tradingbot.readthedocs.io",
        "Source Code": "https://github.com/ilcardella/TradingBot",
    },
    classifiers=[
        'License :: OSI Approved :: MIT License'
    ]
)
