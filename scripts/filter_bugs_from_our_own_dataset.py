from tqdm import tqdm

from bug_improving.types.bug import Bugs, Bug
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    """
    从原始数据集中 1. 过滤掉不是product&component set中的bug
                2. 保留status = "CLOSED, RESOLVED, VERIFIED"
                3. 保留 有 steps to reproduce
    """
    product_component_pair_filepath = PathUtil.get_pc_filepath()
    pc_dataset = FileUtil.load_pickle(product_component_pair_filepath)

    # # 从 BUGS_DB = "data/bugs.json"中读取bugs -> Iterator[BugDict]
    # bugs = bugzilla.get_bugs()
    # bugs = FileUtil.load_json("/Users/suyanqi/Downloads/All_bugs/WebExtensions.json")
    # bugs = FileUtil.load_json("/Users/suyanqi/Downloads/All_bugs/Firefox.json")
    # bugs = FileUtil.load_json("/Users/suyanqi/Downloads/All_bugs/Toolkit.json")
    # bugs = FileUtil.load_json("/Users/suyanqi/Downloads/All_bugs/Firefox Build System.json")
    # bugs = FileUtil.load_json("/Users/suyanqi/Downloads/All_bugs/DevTools.json")
    # bugs = FileUtil.load_json("/Users/suyanqi/Downloads/All_bugs/Core.json")
    # bugs = FileUtil.load_json("/Users/suyanqi/Downloads/split_bugs_Core/Core_3.json")
    bugs = FileUtil.load_json("/Users/suyanqi/Downloads/all_filtered_bugs/our_bugs.json")

    bug_list = []
    # bug_dict_list = []

    for bug_dict in tqdm(bugs, ascii=True):
        # if bug["id"] == 1711924:
        #     continue
        # add Notes section in description.from_text(bug.description.text)
        bug = Bug.from_dict(bug_dict)

        if bug.product_component_pair in pc_dataset:
            if bug.status == 'CLOSED' or bug.status == 'RESOLVED' or bug.status == 'VERIFIED':
                if bug.description and "steps to reproduce" in bug.description.text.lower():
                    # bug_dict_list.append(bug_dict)
                    bug_list.append(bug)

    filtered_bugs = Bugs(bug_list)
    # for bug in filtered_bugs:
    #     print(bug)
        # break
    filtered_bugs.overall_bugs()

    # FileUtil.dump_json("/Users/suyanqi/Downloads/All_bugs/filtered_WebExtensions.json", bug_dict_list)
    # FileUtil.dump_json("/Users/suyanqi/Downloads/All_bugs/filtered_Firefox.json", bug_dict_list)
    # FileUtil.dump_json("/Users/suyanqi/Downloads/All_bugs/filtered_Toolkit.json", bug_dict_list)
    # FileUtil.dump_json("/Users/suyanqi/Downloads/All_bugs/filtered_Firefox Build System.json", bug_dict_list)
    # FileUtil.dump_json("/Users/suyanqi/Downloads/All_bugs/filtered_DevTools.json", bug_dict_list)
    # FileUtil.dump_json("/Users/suyanqi/Downloads/All_bugs/filtered_Core.json", bug_dict_list)
    # FileUtil.dump_json("/Users/suyanqi/Downloads/split_bugs_Core/filtered_Core_3.json", bug_dict_list)
    # FileUtil.dump_json("/Users/suyanqi/Downloads/split_bugs_Core/filtered_Core_3.json", bug_dict_list)

    # filtered_bugs_filepath = PathUtil.get_filtered_bugs_filepath()
    # FileUtil.dump_pickle(filtered_bugs_filepath, filtered_bugs)
