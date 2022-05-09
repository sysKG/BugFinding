import logging

from tqdm import tqdm

from bug_improving.types.bug import Bug
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    """
    从原始数据集中  1. 过滤掉不是product&component set中的bug
    """
    product_component_pair_filepath = PathUtil.get_pc_filepath()
    pc_dataset = FileUtil.load_pickle(product_component_pair_filepath)

    bugs = FileUtil.load_json(PathUtil.get_bugs_filepath("our_original_bugs"))

    bug_list = []
    logging.warning(f"filter {len(bugs)} bugs by pc")
    for bug in tqdm(bugs, ascii=True):
        # add Notes section in description.from_text(bug.description.text)
        bug_object = Bug.from_dict(bug)

        if bug_object.product_component_pair in pc_dataset:

            bug_list.append(bug)

    FileUtil.dump_json(PathUtil.get_bugs_filepath("our_bugs"), bug_list)
    logging.warning(f"{len(bug_list)} bugs left")

