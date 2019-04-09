import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from gui import Ui_MainWindow
from kernel import SaverKernel


class MainWindow(QMainWindow):
    def __init__(self):
        # initiate
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # define data
        self.game_dir = ''
        self.save_name = ''
        self.selected_backups = []
        self.kernel = SaverKernel()
        self.backup_timer = QTimer(self)
        self.binding()
        self.init_table()
        # define shortcut
        QShortcut(QKeySequence('delete'), self, self.delete_backup)

    # bind the ui elements signal to corresponding actions(slot functions)
    def binding(self):
        self.ui.B_choose_dir.clicked.connect(self.choose_dir)
        self.ui.LE_choose_dir.returnPressed.connect(self.update_dir)
        self.ui.B_choose_dir_confirm.clicked.connect(self.update_dir)
        self.ui.S_save_name.currentIndexChanged.connect(self.update_save)
        self.ui.LE_comment.returnPressed.connect(self.backup)
        self.ui.B_backup.clicked.connect(self.backup)
        self.ui.B_reload.clicked.connect(self.reload)
        self.ui.B_delete.clicked.connect(self.delete_backup)
        self.ui.B_delete_f.clicked.connect(self.delete_f)
        self.ui.backup_table.itemSelectionChanged.connect(self.backup_selected)
        self.ui.SB_auto_time.valueChanged.connect(self.auto_available_control)
        self.ui.B_auto_control.clicked.connect(self.auto_control)
        self.backup_timer.timeout.connect(self.auto_backup)

    # initialize backup table
    def init_table(self):
        table = self.ui.backup_table
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSortingEnabled(True)
        header_list = ['', 'backup time', 'last reload', 'comment']
        table.setHorizontalHeaderLabels(header_list)
        table.horizontalHeader().setFixedHeight(30)
        width_list = [0, 150, 150, 250]
        for i, width in enumerate(width_list):
            table.horizontalHeader().resizeSection(i, width)
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)

    # fill the table with backup info
    # this function should be called every time backup situation changed
    def render_table(self):
        self.ui.backup_table.clearContents()
        # if there's no backup, quit the render process
        if not self.kernel.save_list():
            return
        backup_cnt = len(self.kernel.backup_list())
        self.ui.backup_table.setRowCount(backup_cnt)
        for i, timestamp in enumerate(self.kernel.backup_list()):
            info = self.kernel.backup_info(timestamp)
            is_important = info['is important']
            for j, column in enumerate(['timestamp', 'backup time', 'last reload', 'comment']):
                item = QTableWidgetItem(info[column])
                # color important backup with gray background
                if is_important:
                    item.setBackground(QColor(179, 179, 179))
                self.ui.backup_table.setItem(i, j, item)

    # pop up a dialog to choose game directory
    def choose_dir(self):
        f_name = QFileDialog.getExistingDirectory(self, 'choose', 'c:/Ent')
        if f_name:
            self.ui.LE_choose_dir.setText(f_name)
            self.update_dir()

    # procedure after chosen or changing game directory
    def update_dir(self):
        _dir = self.ui.LE_choose_dir.text()
        try:
            self.game_dir = self.kernel.get_mc_dir(_dir)
            self.kernel.update(self.game_dir)
            # activate save selector
            self.ui.S_save_name.setEnabled(True)
            self.ui.S_save_name.clear()
            self.ui.S_save_name.addItems(self.kernel.save_list())
            # activate backup bottom
            self.ui.B_backup.setEnabled(True)
            # check whether auto-backup bottom should be enabled
            self.auto_available_control()
            self.update_save()
        # pop up a warning dialog if input game directory is incorrect
        except SyntaxError as e:
            QMessageBox.information(self, 'exceptional game dir', str(e),
                                         QMessageBox.Yes, QMessageBox.Yes)
        finally:
            self.ui.LE_choose_dir.setText(self.game_dir.replace('\\','/'))

    # procedure after save is chosen of changed
    def update_save(self):
        self.save_name = self.ui.S_save_name.currentText()
        self.kernel.update(self.game_dir, self.save_name)
        # update table widget
        self.render_table()
        self.auto_control()

    # backup current save
    def backup(self):
        comment = self.ui.LE_comment.text()
        is_important = bool(self.ui.CB_important.checkState())
        self.kernel.backup(comment, is_important)
        # clear comment and is_important
        self.ui.LE_comment.setText('')
        self.ui.CB_important.setChecked(False)
        self.render_table()

    # procedure after backup selection is changed
    def backup_selected(self):
        items = self.ui.backup_table.selectedItems()
        backups = [item.text() for item in items]
        n = int(len(backups) / 4)
        self.selected_backups = [backups[4 * k] for k in range(n)]
        self.ui.B_reload.setEnabled(n == 1)
        self.ui.B_delete.setEnabled(n > 0)
        self.ui.B_delete_f.setEnabled(n > 1)

    # judge if auto-backup start/stop bottom should be enabled
    def auto_available_control(self):
        self.ui.B_auto_control.setEnabled(self.ui.B_backup.isEnabled() and int(self.ui.SB_auto_time.text()))

    # react to the click of start/stop bottom
    def auto_control(self):
        if not self.backup_timer.isActive():
            minutes = int(self.ui.SB_auto_time.text())
            if minutes and self.ui.B_backup.isEnabled():
                self.backup_timer.start(60000 * minutes)
                minutes = int(self.ui.SB_auto_time.text())
                next_backup_time = str(datetime.now() + timedelta(minutes=minutes))[2:19]
                self.ui.statusbar.showMessage('Next auto backup at: ' + next_backup_time)
        else:
            self.backup_timer.stop()
            self.ui.statusbar.clearMessage()

    # encapsulation of auto-backup process
    def auto_backup(self):
        self.kernel.backup(comment='Auto', is_important=False)
        secs = int(self.ui.SB_auto_time.text())
        next_backup_time = str(datetime.now() + 2 * timedelta(seconds=secs))[2:19]
        self.ui.statusbar.showMessage('Next auto backup at: ' + next_backup_time)
        self.render_table()

    def reload(self):
        selected_backup = self.selected_backups[0]
        self.kernel.reload(selected_backup)
        self.render_table()

    def delete_backup(self):
        for backup in self.selected_backups:
            if not self.kernel.backup_info(backup)['is important']:
                self.kernel.delete(backup)
        self.render_table()

    def delete_f(self):
        for backup in self.selected_backups:
            self.kernel.delete(backup)
        self.render_table()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MyWin = MainWindow()
    MyWin.show()
    sys.exit(app.exec())
