from setuptools import setup, find_packages
from Experiment import __version__

setup(name="Experiment", 
    version=__version__,
    url='https://github.com/friedforfun/Dissertation',
    author='Sam Fay-hunt',
    author_email='sf52@hw.ac.uk',
    scripts=['start_benchmarker', 'start_compresser'],
    packages=find_packages()
)