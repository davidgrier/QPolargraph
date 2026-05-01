from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QPolargraph.hardware.Polargraph import Polargraph


class QPolargraphWidget(QInstrumentWidget):

    '''Widget for controlling a polargraph scanner.

    Connects a :class:`~QPolargraph.Polargraph.Polargraph` device to
    the ``PolargraphWidget.ui`` layout via :class:`QInstrumentWidget`.
    Hardware is located automatically at startup; if none is found, the
    widget offers to flash the acam3 firmware onto any detected Arduino
    via :class:`~QPolargraph.FlashFirmware.FlashDialog`, then retries
    the connection.  If no Arduino is present or the user declines, the
    widget falls back to :class:`~QPolargraph.hardware.fake.FakePolargraph`.
    Set ``QPolargraphWidget._fake = True`` before instantiation to skip
    the hardware search and flash offer entirely.
    '''

    UIFILE = 'PolargraphWidget.ui'
    INSTRUMENT = Polargraph
    _fake: bool = False

    def __init__(self, *args, **kwargs) -> None:
        if type(self)._fake:
            kwargs.setdefault('device', self._fakeCls()())
        super().__init__(*args, **kwargs)
        if not self.device.isOpen() and not type(self)._fake:
            self._tryFlash()
        if not self.device.isOpen():
            self.device = self._fakeCls()()

    def _tryFlash(self) -> None:
        '''Offer to flash acam3 firmware if an Arduino is detected.

        Opens :class:`~QPolargraph.FlashFirmware.FlashDialog` when at
        least one Arduino-like device is found on a serial port.  If the
        flash succeeds the dialog accepts and this method attempts a new
        :class:`~QPolargraph.Polargraph.Polargraph` connection after a
        2-second boot delay; on success ``self.device`` is replaced with
        the live instrument.
        '''
        import time
        from qtpy import QtWidgets
        from QPolargraph.FlashFirmware import FlashDialog, find_arduinos
        if not find_arduinos():
            return
        message = ('acam3 firmware not detected on the connected Arduino. '
                   'Flash the firmware to connect.')
        dialog = FlashDialog(self, message=message)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            time.sleep(2)  # wait for Arduino to reboot after flashing
            device = Polargraph()
            if device.isOpen():
                self.device = device


if __name__ == '__main__':
    QPolargraphWidget.example()
