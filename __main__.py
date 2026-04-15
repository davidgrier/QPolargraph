import sys
from qtpy.QtWidgets import QApplication
from QPolargraph.QScanner import QScanner


def main() -> None:
    '''Launch the QPolargraph scanner application.'''
    app = QApplication.instance() or QApplication(sys.argv)
    scanner = QScanner()
    scanner.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
