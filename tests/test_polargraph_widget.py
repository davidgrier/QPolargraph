import pytest
from QPolargraph.hardware.QPolargraphWidget import QPolargraphWidget
from QPolargraph.hardware.fake import FakePolargraph


@pytest.fixture
def widget(qtbot):
    w = QPolargraphWidget(device=FakePolargraph())
    qtbot.addWidget(w)
    return w


def test_widget_creates(widget):
    assert widget is not None


def test_widget_device_is_open(widget):
    assert widget.device.isOpen()


def test_fake_device_is_fake_polargraph(widget):
    assert isinstance(widget.device, FakePolargraph)


def test_widget_has_property_changed_signal(widget):
    assert hasattr(widget, 'propertyChanged')
