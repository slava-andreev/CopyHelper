import subprocess, os, pathlib, time, enum
from datetime import datetime
from operator import itemgetter
from pathlib import Path

from rich.live import Live
from options import Options
import log, utils, console_ui
from log import logger
from rich import print

ROBOCOPY_LOG = 'logs\\robocopy_log.txt'
ROBOCOPY_LOG_PREV = 'logs\\robocopy_log_prev.txt'
MIRROR = '/MIR /R:2 /W:5 /NFL /NDL /NP'
FILES_ONLY = '/R:2 /W:5 /NFL /NDL /NP'


def generate_destination_timestamp():
    return datetime.strftime(datetime.now(), '%d%m%y_%H%M')


def find_folders(path, prefix):
    folders = [f for f in os.scandir(path) if f.is_dir() and f.name.upper().startswith(prefix.upper())]

    result = []
    for item in folders:
        try:
            dt = datetime.strptime(item.name[len(prefix):], '%d%m%y_%H%M')
            result.append((dt, item.path))
        except ValueError:
            pass
    return [x[1] for x in sorted(result, key=itemgetter(0))]


class TaskStatus(enum.Enum):
    NEW = 'New'
    RUNNING = 'Running'
    COMPLETED = 'Completed'


class CopyTask:

    def __init__(self, source: str, destination: str, files_only=False, final_validation=False, size=0, files_number=0):
        self.source = source
        self.destination = destination
        self.files_only = files_only
        self.status = TaskStatus.NEW
        self.start_time = None
        self.finish_time = None
        self.final_validation = final_validation
        self.size = size
        self.name = self._generate_name()
        self.files_number = files_number


    def _generate_name(self):
        return f'Backup validation' if self.final_validation else self.source


class BackupRun:

    def __init__(self, options_filename):
        self.destination = None
        self.ui = None
        self.options: Options = Options(options_filename)
        self.source = self.options.source
        self.news = []
        self.last_news_update = None
        self.news_index = 0
        self.tasks: list[CopyTask] = []
        self.total_size = 0
        self.total_files = 0

    def update_news(self):
        now = datetime.now()
        if (not self.last_news_update or (now - self.last_news_update).seconds > 3) and self.news_index < len(
                self.news):
            self.last_news_update = now
            self.ui.news_panel.renderable = '\n'.join(self.news[self.news_index:self.news_index + 3])
            self.news_index += 1
        pass

    def copy_async(self, task: CopyTask, log_file):
        options = FILES_ONLY if task.files_only else MIRROR
        command = f'robocopy "{task.source}" "{task.destination}" {options}'
        return subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT, text=True, encoding='cp866')

   #          if process.poll() > 8:
   #              print(
   #                  f'\n[red]ERROR CODE: {process.poll()} Report to system admin or check last_robocopy_run.txt[/red]\n')
   #              logger.error(
   #                  f"Robocopy failed with code {process.poll()}, please see last_robocopy_run.txt for details")
   # #         diff = utils.calculate_time_diff(start_time, datetime.now())
    #        logger.info(f'{task.source} {'(files)' if task.files_only else ''}: {diff}')


    def copy(self, task: CopyTask):
        start_time = datetime.now()
        options = FILES_ONLY if task.files_only else MIRROR
        command = f'robocopy "{task.source}" "{task.destination}" {options}'

        with open(ROBOCOPY_LOG, 'a', encoding='UTF-8') as robocopy_log:
            with subprocess.Popen(command, stdout=robocopy_log, stderr=subprocess.STDOUT, text=True,
                                  encoding='cp866') as process:
                task_id = self.ui.start_job(task.name) if task.final_validation==True else -1
                ticks = 0
                while process.poll() is None:
                    if ticks % 10 == 0:
                        self.update_news()

                    if task_id < 0 and ticks > 1:  # ~0.2 sec
                        task_id = self.ui.start_job(task.name)

                    time.sleep(0.1)
                    ticks += 1

                self.ui.complete_job(task_id)

                if process.poll() > 8:
                    print(
                        f'\n[red]ERROR CODE: {process.poll()} Report to system admin or check last_robocopy_run.txt[/red]\n')
                    logger.error(
                        f"Robocopy failed with code {process.poll()}, please see last_robocopy_run.txt for details")
                diff = utils.calculate_time_diff(start_time, datetime.now())
                logger.info(f'{task.source} {'(files)' if task.files_only else ''}: {diff}')

    def _create_tasks_recurse(self, source: str, destination: str, iteration: int):
        if iteration > 0:
            folders = []
            files_size = 0
            file_number = 0
            for entry in os.scandir(source):
                if entry.is_file():
                    files_size += entry.stat().st_size
                    file_number += 1
                else:
                    folders.append(entry.name)

            if file_number > 0:
                self.tasks.append(CopyTask(source, destination, files_only=True, size=files_size, files_number=file_number))

            for folder in folders:
                self._create_tasks_recurse(f'{source}\\{folder}', f'{destination}\\{folder}', iteration - 1)
        else:
            dir_info = utils.get_dir_size_files_num(source)
            self.tasks.append(
                CopyTask(source, destination, files_only=False, size=dir_info[0], files_number=dir_info[1]))

    def create_tasks(self):
        self.destination = self.generate_destination_name()
        source_info = utils.get_dir_size_files_num(self.source)
        self.total_size = source_info[0]
        self.total_files = source_info[1]


        self._create_tasks_recurse(self.source, self.destination, self.options.level)
        self.tasks.append(CopyTask(self.source, self.destination, final_validation=True, size=self.total_size,
                                   files_number=self.total_files))

    def copy_dir(self):
        self.ui = console_ui.CopyHelperUI(self.source, self.destination)
        with Live(self.ui.table, refresh_per_second=5):
            self.update_news()

            self.ui.overall_progress.add_task("Jobs completed", total=len(self.tasks))

            for task in self.tasks:
                self.copy(task)

            self.validate_result()

    def validate_result(self):
        source_info = utils.get_dir_size_files_num(self.source)
        dest_info = utils.get_dir_size_files_num(self.destination)
        self.ui.create_check_table(source_info, dest_info)
        logger.info(f'Source total size     : {source_info[0]:,}')
        logger.info(f'Destination total size: {dest_info[0]:,}')

    def generate_destination_name(self):
        d_prefix_path = Path(self.options.destination)
        if d_prefix_path.is_mount():
            print(f'[red]{self.options.backups} is a disk, directory is expected[/red]')
            exit()  # todo fix -> exception? log?

        dest_mid = 'Weekly' if datetime.now().weekday() == 0 else 'Daily'

        full_dest_name = f'{d_prefix_path}_{dest_mid}_{generate_destination_timestamp()}'
        full_dest_path = Path(full_dest_name)

        folders = find_folders(str(d_prefix_path.parent), f'{d_prefix_path.name}_{dest_mid}_')
        for dir_name in folders:
            print(f'Existing backup found: [green]{dir_name}[/green]')

        if not folders:
            print(f'No existing backups')

        if len(folders) >= self.options.backups and not full_dest_path.exists():
            old_path_name = folders[0]
            print(f'Renaming [green]{old_path_name}[/green] to [green]{full_dest_name}[/green]')
            Path(old_path_name).rename(full_dest_path)
        pathlib.Path(full_dest_name).mkdir(exist_ok=True)
        return full_dest_name

    def start(self):
        self.news = utils.get_news()

        self.create_tasks()

        print(
            f'\n------   Backup started from [green]{self.source}[/green] to [green]{self.destination}[/green]   ------\n')
        logger.info(f"*** Backup started from {self.source} to {self.destination}")

        diff = utils.time_diff(self.copy_dir)

        print(f'\n------   Backup finished: {diff}   ------')
        logger.info(f"*** Backup finished: {diff}\n")


def roll_robocopy_logs():
    prev = Path(ROBOCOPY_LOG_PREV)
    current = Path(ROBOCOPY_LOG)
    if prev.exists():
        prev.unlink()
    if current.exists():
        current.rename(prev)


if __name__ == '__main__':
    log.init_logging()
    roll_robocopy_logs()
    BackupRun('CopyHelperConfig.json').start()
