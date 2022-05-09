from tqdm import tqdm

from bug_improving.types.for_github.bug import Bug, Bugs
from bug_improving.utils.file_util import FileUtil

if __name__ == "__main__":
    """
    transform bugs into Bugs for eclipse
    """

    bugs = FileUtil.load_json("/Users/suyanqi/Desktop/product_json_part1/BIRT.json")

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
