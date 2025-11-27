import os
from datetime import datetime
import requests
from xml.dom.minidom import parseString

def get_number_of_dirs(path, iteration):
    dirs = 1
    if iteration >= 0:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_dir():
                    dirs += get_number_of_dirs(entry.path, iteration - 1)
    else:
        return 0
    return dirs

def get_dir_size_date(path: str, recursive: bool):
    files_size = 0
    max_mod_date = 0
    with os.scandir(path) as items:
        for entry in items:
            if entry.is_file():
                stat = entry.stat()
                files_size += stat.st_size
                max_mod_date = max (max_mod_date, stat.st_ctime, stat.st_mtime)
            elif recursive and entry.is_dir():
                 info = get_dir_size_date(entry.path, True)
                 files_size += info[0]
                 max_mod_date = max(max_mod_date, info[1])

    return files_size, max_mod_date

def get_dir_size_files_num(path):
    total = (0, 0)
    with os.scandir(path) as items:
        for entry in items:
            if entry.is_file():
                total = (total[0] + entry.stat().st_size, total[1] + 1)
            elif entry.is_dir():
                x = get_dir_size_files_num(entry.path)
                total = (total[0] + x[0], total[1] + x[1])
    return total

def time_diff(func, *args, **kw):
    start = datetime.now()
    func(*args, **kw)
    finish = datetime.now()
    return calculate_time_diff(start, finish)

def calculate_time_diff(start, finish):
    diff = divmod((finish - start).seconds, 60)
    if diff[0] == 0:
        return f'{diff[1]} sec'
    else:
        return f'{diff[0]} min {diff[1]} sec'

def get_news() -> list[str]:
    result = []
    try:
        response = requests.get('https://www.vedomosti.ru/rss/news.xml')
        response.encoding = "UTF-8"
        document = parseString(response.text)
        for item in document.getElementsByTagName('item'):
            titles = item.getElementsByTagName('title')
            pub_date = item.getElementsByTagName('pubDate')
            news = titles[0].firstChild.data
            try:
                date = datetime.strptime(pub_date[0].firstChild.data[5:22], '%d %b %Y %H:%M')
            except ValueError:
                date = ''
            result.append( f'[yellow]{date:%d %b %H:%M}[/yellow] {news}')
    except:
        pass #todo add logging
    return result
