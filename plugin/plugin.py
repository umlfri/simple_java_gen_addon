from PyQt5.QtWidgets import QApplication

from org.umlfri.api.main_loops.qt import QtMainLoop
from exporter import Exporter


def get_main_loop():
    return QtMainLoop()


def plugin_main(app):
    QApplication.instance().setQuitOnLastWindowClosed(False)
    app.actions["export"].triggered.connect(Exporter(app).export)
