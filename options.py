import json

def load_json(options_filename):
    with open(options_filename, mode='r', encoding='utf-8-sig') as file:
        return json.load(file)

class Options:

    def __init__(self, file_path):
        self._options = load_json(file_path)

    @property
    def source(self) -> str:
        return self._options['source']

    @property
    def destination(self) -> str:
        return self._options['destination']

    @property
    def level(self) -> int:
        return self._options['level']

    @property
    def backups(self) -> int:
        return self._options['number_of_backups']
