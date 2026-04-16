from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QPolargraph.Polargraph import Polargraph


class QPolargraphWidget(QInstrumentWidget):

    '''Widget for controlling a polargraph scanner.

    Connects a :class:`~QPolargraph.Polargraph.Polargraph` device to
    the ``PolargraphWidget.ui`` layout via :class:`QInstrumentWidget`.
    Hardware is located automatically at startup; if none is found the
    widget falls back to :class:`~QPolargraph.fake.FakePolargraph`.
    '''

    UIFILE = 'PolargraphWidget.ui'
    INSTRUMENT = Polargraph

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.device.isOpen():
            self.device = self._fakeCls()()


if __name__ == '__main__':
    QPolargraphWidget.example()
