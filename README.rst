mongo-connector-elastic-doc-manager
==================================

Elastic Doc Manager for the mongo-connector tool

Usage
-----

install via::

    python setup.py install

start the mongo connector with::

    mongo-connector -df elastic_doc_manager    

alternatively, if you download this module, you can 
start the connector with::

    mongo-connector -d <path_to>/elastic_doc_manager.py

Notes
-----

Previously this was included as part of the mongo-connector package.
The purpose of the separation is to encourage users to install plugins
for mongo-connector with pip as opposed to passing in source files.
However, it is still possible to do that with this module (see usage).
