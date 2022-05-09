from tqdm import tqdm

from bug_improving.types.bug import Bug, Bugs
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":

    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_filepath())
    bugs.overall_bugs()

    # bugs = FileUtil.load_json(PathUtil.get_bugs_filepath("our_bugs"))
    # bug_list = []
    # for bug in tqdm(bugs, ascii=True):
    #     # add Notes section in description.from_text(bug.description.text)
    #     bug = Bug.from_dict(bug)
    #     bug_list.append(bug)
    # bugs = Bugs(bug_list)
    # bugs.overall_bugs()
