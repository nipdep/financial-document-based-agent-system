from setuptools import setup, find_packages

setup(
    name="Finacial-agent",  # different name to avoid conflict with main library
    version="0.1.0",
    packages=find_packages(),  # automatically finds chatgenie/ inside src
    install_requires=[
        "openai",
        "langchain<0.1.0",
        "langchain_community<0.1.0",
        "icecream",
        "chromadb",
    ],
)