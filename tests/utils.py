from contextlib import contextmanager

import pytest


@contextmanager
def not_raises(e=None, msg=None):
    if e is None:
        exception = Exception
    try:
        yield None
    except exception as ex:
        pytest.fail(msg=msg or 'Raises %s' % ex)

