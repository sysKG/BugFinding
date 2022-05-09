import logging
from pathlib import Path

from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.graph_util import GraphUtil
from config import DATA_DIR

if __name__ == "__main__":
    logging.warning("Loading bugs...")
    bugs = FileUtil.load_pickle(Path(DATA_DIR, "firefox_about_logins_bugs_with_step_object.json"))
    GraphUtil.get_index_cluster_dict(bugs)
    GraphUtil.get_steps(bugs)
    GraphUtil.get_index_cluster_expected_actual_result_dict()

    while True:
        search_input = input("Please input the cluster_index: ")
        bugid_stepid_expected_actual_result_list = GraphUtil.INDEX_CLUSTER_EXPECTED_ACTUAL_RESULT_DICT[int(search_input)]
        if bugid_stepid_expected_actual_result_list:
            for bugid_stepid_expected_actual_result in bugid_stepid_expected_actual_result_list:
                print(bugid_stepid_expected_actual_result)
