from setuptools import setup, find_packages

setup(
    name="crypto_trading_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-binance>=1.0.16",
        "pandas>=2.0.0",
        "numpy>=1.24.3",
        "scikit-learn>=1.2.2",
        "ta>=0.10.2",
        "python-dotenv>=1.0.0",
        "matplotlib>=3.7.1",
        "seaborn>=0.12.2",
    ],
    author="Seu Nome",
    author_email="seu.email@exemplo.com",
    description="Bot de trading de criptomoedas com IA",
    keywords="crypto, trading, bot, machine learning",
    python_requires=">=3.8",
)
