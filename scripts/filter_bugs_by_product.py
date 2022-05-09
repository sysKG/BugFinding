import csv
from pathlib import Path

from bug_improving.types.bug import Bugs
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil
from config import DATA_DIR

if __name__ == "__main__":
    filtered_bugs = []
    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_filepath())
    print(bugs.get_length())
    for bug in bugs:
        if bug.product_component_pair.product != "Core":
            filtered_bugs.append(bug)

    filtered_bugs = Bugs(filtered_bugs)
    print(filtered_bugs.overall_bugs())
    FileUtil.dump_pickle(Path(DATA_DIR, "filtered_bugs_without_core.json"), filtered_bugs)
