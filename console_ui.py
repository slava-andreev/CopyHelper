from rich import box
from rich.panel import Panel
from rich.progress import TaskID, Progress, BarColumn, TimeElapsedColumn, MofNCompleteColumn, SpinnerColumn
from rich.table import Table

TOP = box.Box(
    " ── \n"
    "    \n"
    "    \n"
    "    \n"
    "    \n"
    "    \n"
    "    \n"
    "    \n"
)


class CopyHelperUI:

    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.job_progress = None
        self.overall_progress = None
        self.news_panel = None
        self.table = self.build_table()
        self.completed_jobs = 0

    def create_check_table(self, source_info, dest_info):
        check_table = Table(box=None, expand=True)
        check_table.add_column("\nFolder")
        check_table.add_column("\nSize, bytes")
        check_table.add_column("\nFiles")

        color_size = '[green]' if source_info[0] == dest_info[0] else '[red]'
        color_files = '[green]' if source_info[1] == dest_info[1] else '[red]'

        check_table.add_row(self.source, f'{color_size}{source_info[0]:,d}', f'{color_files}{source_info[1]:,d}')
        check_table.add_row(self.destination, f'{color_size}{dest_info[0]:,d}', f'{color_files}{dest_info[1]:,d}')
        self.table.add_row(Panel(check_table, box=TOP, title="[b]Backup validation", border_style="cyan"))

    def build_table(self):
        self.job_progress = Progress(SpinnerColumn(spinner_name='bouncingBar'),
                                     "{task.description}",
                                     TimeElapsedColumn(),
                                     refresh_per_second=1)
        self.overall_progress = Progress("{task.description}",
                                         BarColumn(),
                                         MofNCompleteColumn(),
                                         TimeElapsedColumn(),
                                         refresh_per_second=5)

        progress_table = Table.grid(padding=1, expand=True)
        self.news_panel = Panel("", title="Latest news from Vedomosti", border_style="red", box=TOP)
        progress_table.add_row(self.news_panel)
        progress_table.add_row(
            Panel(self.overall_progress, title="Overall Progress (Folders)", border_style="blue", box=TOP))
        progress_table.add_row(Panel(self.job_progress, title="[b]Jobs", border_style="green", box=TOP))
        return progress_table

    def start_job(self, title) -> TaskID:
        return self.job_progress.add_task(title, refresh_per_second=1, total=1)

    def complete_job(self, task_id=-1):
        if task_id >= 0:
            self.job_progress.advance(task_id)

        self.completed_jobs += 1
        self.overall_progress.update(0, completed=self.completed_jobs)
