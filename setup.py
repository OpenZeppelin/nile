from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()

setup(
    name = 'cairo-nile',
    version = '0.0.3',
    author = 'Martin Triay',
    author_email = 'martriay@gmail.com',
    license = 'MIT',
    description = 'StarkNet/Cairo development toolbelt',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = 'https://github.com/martriay/nile',
    py_modules = [''],
    packages = find_packages(),
    install_requires = [requirements],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    entry_points = '''
        [console_scripts]
        nile=nile.main:cli
    '''
)
