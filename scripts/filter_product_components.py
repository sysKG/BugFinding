from tqdm import tqdm

from bug_improving.types.product_component_pair import ProductComponentPair, ProductComponentPairs
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    # filepath = PathUtil.get_train_bugs_filepath()
    filepath = PathUtil.get_pc_filepath()
    pcs = FileUtil.load_pickle(filepath)
    # print(type(pcs))
    # filtered_pcs = list()
    # for pc in tqdm(pcs):
    #     if pc.product != "Core":
    #         if pc.product != "Firefox Build System" or pc.component != "Generated Documentation":
    #             filtered_pcs.append(pc)
    # filtered_pcs = ProductComponentPairs(filtered_pcs)
    # for pc in filtered_pcs:
    #     print(pc)
    # print(len(filtered_pcs.product_component_pair_list))
    # #
    # FileUtil.dump_pickle(filepath, filtered_pcs)
    for pc in tqdm(pcs):
        print(pc)
