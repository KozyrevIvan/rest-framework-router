from setuptools import setup, find_packages
from os.path import join, dirname
import rest_framework_router

setup(
    name='rest-framework-router',
    version=rest_framework_router.__version__,
    author=rest_framework_router.__author__,
    url='https://github.com/KozyrevIvan/rest-framework-router',
    license=rest_framework_router.__license__,
    zip_safe=False,
    packages=find_packages(exclude=['tests','example']),
    setup_requires=['django>=2.2.17','djangorestframework>=3.12.2'],
    long_description=open(join(dirname(__file__), 'README.md')).read(),
)