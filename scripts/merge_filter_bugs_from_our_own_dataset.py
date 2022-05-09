from tqdm import tqdm

from bug_improving.types.bug import Bugs, Bug
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    """
    merge bugs (core, firefox, toolkit,...)
    """
    bugs_1 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_WebExtensions.json")
    bugs_2 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_Firefox.json")
    bugs_3 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_Toolkit.json")
    bugs_4 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_Firefox Build System.json")
    bugs_5 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_DevTools.json")
    bugs_6 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_Core_0.json")
    bugs_7 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_Core_1.json")
    bugs_8 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_Core_2.json")
    bugs_9 = FileUtil.load_json("/Users/suyanqi/Downloads/All_filtered_bugs/filtered_Core_3.json")

    bugs = list()
    bugs.extend(bugs_1)
    bugs.extend(bugs_2)
    bugs.extend(bugs_3)
    bugs.extend(bugs_4)
    bugs.extend(bugs_5)
    bugs.extend(bugs_6)
    bugs.extend(bugs_7)
    bugs.extend(bugs_8)
    bugs.extend(bugs_9)

    FileUtil.dump_json("/Users/suyanqi/Downloads/All_filtered_bugs/our_bugs.json", bugs)

