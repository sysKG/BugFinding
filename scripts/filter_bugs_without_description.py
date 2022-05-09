from tqdm import tqdm

from bug_improving.types.for_github.bug import Bugs
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil


if __name__ == "__main__":
    """
    从数据集中 1. 只保留description为空的bugs
    """
    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_filepath())

    bug_list = []

    for bug in tqdm(bugs, ascii=True):
        if bug.description.text.strip() == '':
            bug_list.append(bug)
            # print(f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}")
            # print(bug.description)

    filtered_bugs = Bugs(bug_list)
    filtered_bugs.overall_bugs()

    # filtered_bugs_filepath = PathUtil.get_filtered_bugs_without_stp_filepath()
    # FileUtil.dump_pickle(filtered_bugs_filepath, filtered_bugs)
