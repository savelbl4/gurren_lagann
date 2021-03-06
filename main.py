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


class Merge:
    def __init__(self, title_dir: str):
        self.home_dir = os.getcwd()
        self.tree_of_dir = []
        self.files = []
        self.change_dir(title_dir)
        self.create_tree()
        self.check_dir()
        self.list_on_merge = {}
        self.create_key()
        self.build_hash()
        for key in self.list_on_merge:
            pattern = re.compile(key+'([\[\]A-Za-z0-9._\- ]+)')
            # return pprint(self.list_on_merge)
            match = pattern.search(self.list_on_merge[key]['audio'])
            title = match.group(1).strip()
            print(f'{key}\t{title}')

    @staticmethod
    def change_dir(path):
        """переходим в дирректорию
        """
        os.chdir(path)

    @staticmethod
    def change_spaces(src: str):
        """заменяем пробелы на подчёркивания
        """
        dst = '_'.join(src.split(' '))
        os.rename(src, dst)
        return dst

    @staticmethod
    def change_underline(src: str):
        """заменяем подчёркивания на пробелы
        """
        dst = ' '.join(src.split('_'))
        os.rename(src, dst)
        return dst

    def create_tree(self, pth: str = '.'):
        """создаём дерево каталогов попутно заменяя пробелы
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

    def check_file(self, file_name, num=None) -> dict:
        """получить данные из файле
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

    def chek_streams(self, key, each, file):
        # print(file.get('format').get('filename'))
        for stream in file.get('streams'):
            if stream.get('codec_type') == 'video':
                self.list_on_merge[key].update([('video', each)])
            if stream.get('codec_type') == 'audio' and 'rus' in stream.get('tags')['language']:
                self.list_on_merge[key].update([('audio', each)])
                # print(stream)

    def create_key(self):
        """создаём ключи по названиям видео в корневом каталоге
        TODO: регулярка не идеальна
        """
        for each in self.files:
            if len(each.split('\\')) == 2:
                pattern = re.compile(r'([A-Za-z0-9._\- ]+\d)[. ][\[(A-Za-z]')
                match = pattern.search(each)
                if match:
                    title = match.group(1).strip()
                    if not self.list_on_merge.get(title):
                        self.list_on_merge.update([(title, {})])

    def build_hash(self):
        """собрали значения ключей
        TODO: дорожек с озвучкой может быть несколько!
        """
        for key in self.list_on_merge.keys():
            pattern = re.compile(key)
            for each in self.files:
                match = pattern.search(each)
                if match:
                    file = self.check_file(each)
                    # return print(json.dumps(file))
                    if file.get('format').get('nb_streams') == 1:
                        stream = file.get('streams')[0]
                        # print(file.get('format').get('filename'))
                        if stream.get('codec_type') == 'video':
                            self.list_on_merge[key].update([('video', each)])
                        if stream.get('codec_type') == 'audio':
                            self.list_on_merge[key].update([('audio', each)])
                        if stream.get('codec_type') == 'subtitle':
                            if not self.list_on_merge[key].get('subtitle'):
                                print(self.check_file(each))
                                exit(0)
                                self.list_on_merge[key].update([('subtitle', [each])])
                            else:
                                self.list_on_merge[key]['subtitle'].append(each)
                    else:
                        self.chek_streams(key, each, file)

    def replace_audio(self, video, audio):
        """заменяет дорожку
        """
        merged = ''.join(['replaced_', video])
        subprocess.run(f'ffmpeg -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v copy -shortest output.mp4')

    def add_audio(self, video, audio):
        """добавляет дорожку
        """
        added = '\\added_'.join(video.split('\\'))
        command_array = ['ffmpeg',
                         '-v', 'quiet',
                         '-i', video, '-i', audio,
                         '-map', '0:v', '-map', '1:a', '-map', '0:a',
                         '-c',
                         # '-c:v',
                         'copy', '-shortest',
                         added
                         ]
        line = f'ffmpeg -i {video} -i {audio} -map 0:v -map 1:a -map 0:a -c:v copy -shortest {added}'
        print(command_array)
        subprocess.run(command_array)

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
        """погнали слиять
        """
        for key in self.list_on_merge.keys():
            self.add_audio(
                self.list_on_merge[key]['video'],
                self.list_on_merge[key]['audio']
            )
            send2trash(self.list_on_merge[key]['video'])

    def no(self):
        pprint(self.list_on_merge)


if __name__ == '__main__':
    search_path = input(
                "\nВведи путь.\nИли нажмите Enter чтобы искать в домашнем каталоге: "
            ).strip()
    if not search_path:
        search_path = {
            'Linux': '~/',
            'Darwin': '~/',
            'Windows': f'F:\\Videos\\anime'
        }[platform.system()]
    proj = Merge(search_path)
    answer = input('\n\tну шо, start?\n\t\t\t: ').strip()
    if answer == 'start':
        proj.start()
    if answer == 'no':
        proj.no()
else:
    # proj = Merge('F:\\Videos\\anime\\[Leopard-Raws] Sakura Quest [HDTVRip] [720p]')
    proj = Merge('F:\\Videos\\anime\\Acchi Kocchi')
