from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QPolargraph.hardware.Polargraph import Polargraph


class QPolargraphWidget(QInstrumentWidget):

    '''Widget for controlling a polargraph scanner.

    Connects a :class:`~QPolargraph.Polargraph.Polargraph` device to
    the ``PolargraphWidget.ui`` layout via :class:`QInstrumentWidget`.
    Hardware is located automatically at startup; if none is found the
    widget falls back to :class:`~QPolargraph.hardware.fake.FakePolargraph`.
    Set ``QPolargraphWidget._fake = True`` before instantiation to skip
    the hardware search entirely and use the fake device unconditionally.
    '''

    UIFILE = 'PolargraphWidget.ui'
    INSTRUMENT = Polargraph
    _fake: bool = False

    def __init__(self, *args, **kwargs) -> None:
        if type(self)._fake:
            kwargs.setdefault('device', self._fakeCls()())
        super().__init__(*args, **kwargs)
        if not self.device.isOpen():
            self.device = self._fakeCls()()


if __name__ == '__main__':
    QPolargraphWidget.example()
