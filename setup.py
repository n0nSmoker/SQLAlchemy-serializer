
from distutils.core import setup

setup(name='SQLAlchemy-serializer',
      version='0.91',
      description='Mixin for SQLAlchemy-models serialization without pain',
      author='Y-Bro',
      url='https://github.com/n0nSmoker/SQLAlchemy-serializer.git',
      keywords=['sqlalchemy', 'serialize', 'to_dict', 'JSON'],
      packages=['sqlalchemy_serializer', 'sqlalchemy_serializer.lib'],
      install_requires=[
        'SQLAlchemy',
        'Flask-Babel',
        'Flask-Builder',
        'blinker',
      ]
)


