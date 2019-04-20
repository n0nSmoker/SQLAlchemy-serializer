from distutils.core import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='SQLAlchemy-serializer',
    version='1.1.3',
    description='Mixin for SQLAlchemy-models serialization without pain',
    long_description=long_description,
    long_description_content_type='text/markdown; charset=UTF-8; variant=GFM',
    author='Y-Bro',
    url='https://github.com/n0nSmoker/SQLAlchemy-serializer.git',
    keywords=['sqlalchemy', 'serialize', 'to_dict', 'JSON'],
    packages=['sqlalchemy_serializer', 'sqlalchemy_serializer.lib'],
    install_requires=[
        'SQLAlchemy',
    ]
)



