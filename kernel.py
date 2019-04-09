import os
import shutil
import configparser
from datetime import datetime

save_dir_name = 'saves'
backup_dir_name = 'saves_backup'


class SaverKernel:
    def __init__(self):
        self.game_dir = ''
        self.save_name = ''
        self.info = configparser.ConfigParser()

    def _join_path(self, *folder_name):
        return os.path.join(self.game_dir, *folder_name)

    def _save_dir(self):
        return self._join_path(save_dir_name)

    def _save_pos(self):
        return self._join_path(save_dir_name, self.save_name)

    def _backup_dir(self):
        return self._join_path(backup_dir_name)

    def _info_pos(self):
        return self._join_path(backup_dir_name, self.save_name + '.ini')

    # warning: timestamp must be a string
    def _backup_pos(self, timestamp):
        return os.path.join(self._backup_dir(), timestamp)

    @staticmethod
    def get_mc_dir(_dir):
        _dir = str(_dir)
        if not os.path.isabs(_dir):
            raise SyntaxError('Wrong directory format')
        if not os.path.exists(_dir):
            raise SyntaxError('Directory not found')
        if '.minecraft' in os.listdir(_dir):
            _dir = os.path.join(_dir, '.minecraft')
        while _dir:
            _dir, folder = os.path.split(_dir)
            if folder == '.minecraft':
                _dir = os.path.join(_dir, '.minecraft')
                break
            if not folder:
                raise SyntaxError('this is not a .minecraft directory')
        if save_dir_name not in os.listdir(_dir):
            raise SyntaxError('this folder contain no save directory')
        return _dir

    def save_list(self):
        return os.listdir(self._save_dir())

    def backup_list(self):
        return self.info.sections()

    def backup_info(self, timestamp):
        section = self.info[timestamp]
        return {
            'timestamp':timestamp,
            'backup time':section['time'],
            'last reload':section['last reload'],
            'comment':section['comment'],
            'is important':section.getboolean('is important')
        }

    def update(self, game_dir, save_name=''):
        self.game_dir = game_dir
        if backup_dir_name not in os.listdir(self.game_dir):
            os.mkdir(self._backup_dir())
        if save_name:
            self.save_name = save_name
            self.info.clear()
            self.info.read(self._info_pos())

    def write(self):
        with open(self._info_pos(), 'w') as i:
            self.info.write(i)

    def backup(self, comment='', is_important=False):
        timestamp = str(datetime.now().timestamp())
        readable_time = str(datetime.now())[2:19]
        self.info[timestamp] = {
            'time':readable_time,
            'comment':comment,
            'is important':str(is_important),
            'last reload':''
        }
        shutil.copytree(self._save_pos(), self._backup_pos(timestamp))
        self.write()

    def reload(self, timestamp):
        shutil.rmtree(self._save_pos())
        shutil.copytree(self._backup_pos(timestamp), self._save_pos())
        self.info[timestamp]['last reload'] = str(datetime.now())[2:19]
        self.write()

    def delete(self, timestamp):
        shutil.rmtree(self._backup_pos(timestamp))
        self.info.remove_section(timestamp)
        self.write()

if __name__ == '__main__':
    s = SaverKernel()
    print(s.get_mc_dir('C:/Dev/test/mc1/.mine'))
