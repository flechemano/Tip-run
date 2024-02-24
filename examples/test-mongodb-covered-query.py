"""
This script demonstrates how ``pip-run`` facilitates the
simple execution of complex tasks with their
dependencies.

Run this example with ``pip-run $script``.

It creates a MongoDB instance, and then runs some
assertions against it.

The script uses `jaraco.mongodb
<https://pypi.org/project/jaraco.mongodb>`_ to (maybe)
install and configure an ephemeral instance of MongoDB.

Running this script with ``pip-run``` leaves no trace of its
execution, other than adding packages to the pip
cache (if available), so feel free to give it a try.

This script gets read three times:

- First ``pip-run`` reads it statically to determine the
  dependencies found in ``__requires__`` and
  installs those dependencies in a temp dir.
- Then, the script is executed by a Python interpreter
  which executes the script up to the __main__ block,
  which invokes pytest with the script name as the
  first argument.
- ``py.test`` then runs the test, using the plugins
  from jaraco.mongodb to satisfy the ``mongodb_instance``
  fixture for the test.

Alternately, the script could be
invoked thus:  ``pip-run -- -m pytest $script``, which would
eliminate the need for the ``__main__`` block and
would skip the second processing of the script.
"""

__requires__ = ['pytest', 'jaraco.mongodb>=3.10']

if __name__ == '__main__':
    # invoke pytest on this script
    import sys

    import pytest

    sys.exit(pytest.main(['--noconftest'] + sys.argv))

import itertools
import random

import pytest
from jaraco.mongodb.testing import assert_covered


@pytest.fixture
def docs_in_db(mongodb_instance):
    """
    Install 100 records with random numbers
    """
    conn = mongodb_instance.get_connection()
    coll = conn.test_db.test_coll
    coll.drop()
    coll.create_index('number')
    n_records = 100
    for n in itertools.islice(itertools.count(), n_records):
        doc = dict(number=random.randint(0, 2**32 - 1), value='some value')
        conn.test_db.test_coll.insert_one(doc)
    return coll


def test_records(docs_in_db, mongodb_instance):
    "Test 100 records are present and query is covered"
    # load all the numbers to ensure the index is in RAM
    _hint = 'number_1'
    _filter = {'number': {'$gt': 0}}
    _projection = {'number': True, '_id': False}
    cur = docs_in_db.find(filter=_filter, projection=_projection).hint(_hint)
    assert_covered(cur)

    # consume the cursor for good measure
    docs = list(cur)
    assert len(docs) == 100
