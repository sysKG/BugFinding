from bugbug import bugzilla
from tqdm import tqdm

from bug_improving.types.bug import Bugs, Bug
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    """
    从原始数据集中 1. 过滤掉不是product&component set中的bug
                2. 保留status = "REOPEN"
    """
    product_component_pair_filepath = PathUtil.get_pc_filepath()
    pc_dataset = FileUtil.load_pickle(product_component_pair_filepath)

    # 从 BUGS_DB = "data/bugs.json"中读取bugs -> Iterator[BugDict]
    bugs = bugzilla.get_bugs()

    bug_list = []
    all_bug_num = 0
    for bug in tqdm(bugs, ascii=True):
        bug = Bug.from_dict(bug)
        if bug.product_component_pair in pc_dataset:
            all_bug_num = all_bug_num + 1
            if bug.status == 'REOPENED':
                bug_list.append(bug)
    print(all_bug_num)
    filtered_bugs = Bugs(bug_list)
    filtered_bugs.overall_bugs()

    # filtered_bugs_filepath = PathUtil.get_filtered_bugs_filepath()
    # FileUtil.dump_pickle(filtered_bugs_filepath, filtered_bugs)
