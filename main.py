import os
import re
import json
import platform
import ffmpeg
import subprocess
import mimetypes
# from ffprobe import FFProbe
from send2trash import send2trash
from pprint import pprint
search_path = input(
            "\nВведи путь.\nИли нажмите Enter чтобы искать в домашнем каталоге: "
        ).strip()

if not search_path:
    search_path = {
        'Linux': '~/',
        'Darwin': '~/',
        'Windows': f'E:\\Videos\\anime\\[Kawaiika-Raws] (2020) Ishuzoku Reviewers [BDRip 1920x1080 HEVC FLAC]'
    }[platform.system()]

class Merge:
    def __init__(self, title_dir: str = 'E:\\Videos\\anime\\[Kawaiika-Raws] (2020) Ishuzoku Reviewers [BDRip 1920x1080 HEVC FLAC]'):
        self.home_dir = os.getcwd()
        self.tree_of_dir = []
        self.files = []
        self.change_dir(title_dir)
        self.create_tree()
        self.check_dir()
        self.list_on_merge = {
            # 'video': [],
            # 'audio': [],
            # 'subtitle': [],
            # 'hh': {},
        }
        self.create_key()
        # self.go = self.create_key()

    @staticmethod
    def change_dir(path):
        """
        переходим в дирректорию
        """
        os.chdir(path)

    @staticmethod
    def change_spaces(src: str):
        """
        заменяем пробелы на подчёркивания
        """
        dst = '_'.join(src.split(' '))
        os.rename(src, dst)
        return dst

    @staticmethod
    def change_underline(src: str):
        """
        заменяем подчёркивания на пробелы
        """
        dst = ' '.join(src.split('_'))
        os.rename(src, dst)
        return dst

    def create_tree(self, pth: str = '.'):
        """
        создаём дерево каталогов попутно заменяя пробелы
        """
        if not pth in self.tree_of_dir:
            self.tree_of_dir.append(pth)
        for item in os.listdir(path=pth):
            pth_item = '\\'.join([pth, item])
            # new_pth = self.change_spaces(pth_item)
            new_pth = self.change_underline(pth_item)
            if os.path.isdir(new_pth):
                self.create_tree(new_pth)

    def check_dir(self):
        """
        перебираем содержимое каталогов и записываем пути к файлам
        """
        for pth in self.tree_of_dir:
            for each in os.listdir(path=pth):
                type = str(mimetypes.guess_type(each))
                if re.search(r'video', type) or re.search(r'audio', type):
                    self.files.append('\\'.join([pth, each]))

    def create_key(self):
        """
        создаём ключи по названиям видео в корневом каталоге
        """
        for each in self.files:
            if len(each.split('\\')) == 2:
                pattern = re.compile('] ([A-Za-z0-9._ ]+) \[')
                match = pattern.search(each)
                if match:
                    title = match.group(1)
                    print(title)
                    if not self.list_on_merge.get(title):
                        self.list_on_merge.update([(title, {})])

    def check_file(self, file_name, num = None) -> dict:
        """
        получить данные из файле
        """
        command_array = ['ffprobe',
                         '-v', 'quiet',
                         '-print_format', 'json',
                         '-show_format',
                         '-show_streams',
                         file_name]
        result = subprocess.run(
            command_array,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        k = json.loads(result.stdout)
        if k.get('streams') and num:
            for each in k.get('streams'):
                print(f"{each.get('codec_name')}"
                      f" {each.get('codec_type')}"
                      f" {each.get('tags', '')}")
        return k

        # go = {}
        # if len(self.list['video']) == len(self.list['audio']):
        #     for i in range(len(self.list['video'])):
        #         video = self.change_spaces(self.list['video'][i])
        #         audio = self.change_spaces(self.list['audio'][i])
        #         go.update([(video, audio)])
        # else:
        #     print('количество файлов не совпадает')
        #     exit(1)
        # return go

    def replace_audio(self, video, audio):
        """
        заменяет дорожку
        """
        merged = ''.join(['replaced_', video])
        subprocess.run(f'ffmpeg -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v copy -shortest output.mp4')

    def add_audio(self, video, audio):
        """
        добавляет дорожку
        """
        added = ''.join(['added_', video])
        line = f'ffmpeg -i {video} -i {audio} -map 0:v -map 1:a -map 0:a -c:v copy -shortest {added}'
        print(line)
        subprocess.run(line)

    def mixing_audio(self):
        subprocess.run(
            f'ffmpeg -i video.mkv -i audio.m4a'
            f' -filter_complex "[0:a][1:a]amerge=inputs=2[a]"'
            f' -map 0:v -map "[a]" -c:v copy -ac 2 -shortest output.mkv'
        )

    def nesub(self, video, audio):
        new_name = video.split('\\[Kawaiika-Raws] ')[2]
        input_video = ffmpeg.input(video)
        input_audio = ffmpeg.input(audio)
        ffmpeg.concat()
        ffmpeg.concat(input_video, input_audio, v=1, a=1).output(new_name).run()

    def start(self):
        for key in self.go:
            self.add_audio(key, self.go[key])
            send2trash(key)

proj = Merge(search_path)

# proj.start()