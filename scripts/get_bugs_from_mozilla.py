from pathlib import Path

from tqdm import tqdm

from bug_improving.types.bug import Bug, Bugs
from bug_improving.utils.file_util import FileUtil
from config import DATA_DIR

if __name__ == "__main__":
    """
    transform bugs into Bugs for mozilla
    """

    # bugs = FileUtil.load_json(Path(DATA_DIR, "firefox_bug", "Firefox_about_logins.json"))
    bugs = FileUtil.load_json(Path(DATA_DIR, "firefox_bug", "Firefox_Preferences.json"))

    bug_list = []

    for bug in tqdm(bugs, ascii=True):

        bug = Bug.from_dict(bug)
        try:
            if "steps to reproduce" in bug.description.text.lower():
                bug_list.append(bug)
                # print(bug)
        except:
            pass
    filtered_bugs = Bugs(bug_list)
    filtered_bugs.overall_bugs()

    # filtered_bugs_filepath = PathUtil.get_filtered_bugs_filepath()
    # FileUtil.dump_pickle(filtered_bugs_filepath, filtered_bugs)
