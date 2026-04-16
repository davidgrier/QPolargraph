import pytest
from QPolargraph.fake import FakePolargraph


@pytest.fixture(scope='session', autouse=True)
def qapp_session(qapp):
    '''Ensure a QApplication exists for the whole test session.'''
    return qapp


@pytest.fixture
def polargraph():
    return FakePolargraph(step_delay=0.)
