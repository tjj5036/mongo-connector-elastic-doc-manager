# Copyright 2012 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file will be used with PyPi in order to package and distribute the final
# product.

"""Receives documents from the oplog worker threads and indexes them
    into the backend.

    This file is a document manager for the Elastic search engine, but the
    intent is that this file can be used as an example to add on different
    backends. To extend this to other systems, simply implement the exact
    same class and replace the method definitions with API calls for the
    desired backend.
    """
import time
import logging
import sys

from pyes import ES, ESRange, RangeQuery, MatchAllQuery, TextQuery
from pyes.exceptions import IndexMissingException
from threading import Timer
from urllib2 import urlopen, URLError

def verify_url(url):
    """Verifies the validity of a given url.
    """
    try:
        urlopen(url)
        return True
    except (ValueError, URLError):
        return False

def retry_until_ok(func, args=None):
    """Retry code block until it succeeds.

    If it does not succeed in 60 attempts, the
    function simply exits.
    """

    result = True
    count = 0
    while True:
        try:
            if args is None:
                result = func()
                break
            else:
                result = func(args)
                break
        except:
            count += 1
            if count > 60:
                logging.error('Call to %s failed too many times'
                ' in retry_until_ok' % (func))
                sys.exit(1)
            time.sleep(1)

    return result

class DocManager(object):
    """The DocManager class creates a connection to the backend engine and
        adds/removes documents, and in the case of rollback, searches for them.

        The reason for storing id/doc pairs as opposed to doc's is so that
        multiple updates to the same doc reflect the most up to date version as
        opposed to multiple, slightly different versions of a doc.

        We are using elastic native fields for _id and ns, but we also store
        them as fields in the document, due to compatibility issues.
        """

    def __init__(self, url, auto_commit=True, unique_key='_id'):
        """Verify Elastic URL and establish a connection.
        """

        if verify_url(url) is False:
            raise SystemError
        self.elastic = ES(server=url)
        self.auto_commit = auto_commit
        self.doc_type = 'string'  # default type is string, change if needed
        self.unique_key = unique_key
        if auto_commit:
            self.run_auto_commit()

    def stop(self):
        """ Stops the instance
        """
        self.auto_commit = False

    def upsert(self, doc):
        """Update or insert a document into Elastic

        If you'd like to have different types of document in your database,
        you can store the doc type as a field in Mongo and set doc_type to
        that field. (e.g. doc_type = doc['_type'])

        """

        # There is a problem with ES .90.0 and possibly .90.1 with 
        # indices not be correctly handled.
        # This ensures that an upsert correctly happens

        doc_type = self.doc_type
        index = doc['ns']
        doc[self.unique_key] = str(doc[self.unique_key])
        doc_id = doc[self.unique_key]
        id_query = TextQuery('_id', doc_id)
        elastic_cursor = self.elastic.search(query=id_query, indices=index)

        if elastic_cursor.total == 0:
            self.elastic.index(doc, index, doc_type, doc_id)
        else:  
            self.elastic.update(doc, index, doc_type, doc_id)
        self.elastic.refresh()

    def remove(self, doc):
        """Removes documents from Elastic

        The input is a python dictionary that represents a mongo document.
        """
        try:
            self.elastic.delete(doc['ns'], 'string', str(doc[self.unique_key]))
        except IndexMissingException:
            pass

    def _remove(self):
        """For test purposes only. Removes all documents in test.test
        """
        try:
            self.elastic.delete('test.test', 'string', '')
        except IndexMissingException:
            pass

    def search(self, start_ts, end_ts):
        """Called to query Elastic for documents in a time range.
        """
        res = ESRange('_ts', from_value=start_ts, to_value=end_ts)
        results = self.elastic.search(RangeQuery(res))
        return results

    def _search(self):
        """For test purposes only. Performs search on Elastic with empty query.
        Does not have to be implemented.
        """
        results = self.elastic.search(MatchAllQuery())
        return results

    def commit(self):
        """This function is used to force a refresh/commit.
        """
        retry_until_ok(self.elastic.refresh)

    def run_auto_commit(self):
        """Periodically commits to the Elastic server.
        """
        self.elastic.refresh()

        if self.auto_commit:
            Timer(1, self.run_auto_commit).start()

    def get_last_doc(self):
        """Returns the last document stored in the Elastic engine.
        """

        result = self.elastic.search(MatchAllQuery(), size=1, sort='_ts:desc')
        for item in result:
            return item
