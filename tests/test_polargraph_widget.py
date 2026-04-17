import pytest
from QPolargraph.hardware.QPolargraphWidget import QPolargraphWidget
from QPolargraph.hardware.fake import FakePolargraph


@pytest.fixture
def widget(qtbot):
    QPolargraphWidget._fake = True
    w = QPolargraphWidget()
    QPolargraphWidget._fake = False
    qtbot.addWidget(w)
    return w


def test_widget_creates(widget):
    assert widget is not None


def test_widget_device_is_open(widget):
    assert widget.device.isOpen()


def test_fake_flag_uses_fake_polargraph(qtbot):
    QPolargraphWidget._fake = True
    try:
        w = QPolargraphWidget()
        qtbot.addWidget(w)
        assert isinstance(w.device, FakePolargraph)
    finally:
        QPolargraphWidget._fake = False


def test_fake_flag_resets_after_use(qtbot):
    QPolargraphWidget._fake = True
    w = QPolargraphWidget()
    QPolargraphWidget._fake = False
    qtbot.addWidget(w)
    assert not QPolargraphWidget._fake


def test_widget_has_property_changed_signal(widget):
    assert hasattr(widget, 'propertyChanged')
