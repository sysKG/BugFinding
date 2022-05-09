from pathlib import Path

from tqdm import tqdm

from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil
from config import DATA_DIR

if __name__ == "__main__":
    # filtered_bugs = []
    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_filepath())
    bug_dicts = FileUtil.load_json(PathUtil.get_bugs_filepath("our_bugs"))
    print(bugs.get_length())
    bug_ids = list()
    for bug in bugs:
        bug_ids.append(bug.id)
    bug_dicts_for_baseline = list()
    for bug_dict in tqdm(bug_dicts, ascii=True):
        if bug_dict['id'] in bug_ids:
            bug_dicts_for_baseline.append(bug_dict)

    print(len(bug_dicts_for_baseline))
    FileUtil.dump_json(Path(DATA_DIR, "filtered_bugs_for_baseline.json"), bug_dicts_for_baseline)
