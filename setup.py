from setuptools import setup
import sys

setup(name='mongo-connector-elastic-doc-manager',
      version='1.0.0',
      maintainer='10gen',
      description='Elastic plugin for mongo-connector',
      platforms=['any'],
      author='10gen labs',
      author_email='tyler.jones@10gen.com',
      url='https://github.com/10gen-labs/',
      py_modules=['elastic_doc_manager'],
      install_requires=['pyes'],
      license='OSI Approved :: Apache Software License',
      keywords='mongo-connector',
      entry_points={
          'mongo_connector_plugins': 
            ['elastic_doc_manager = elastic_doc_manager:DocManager']},
      )
