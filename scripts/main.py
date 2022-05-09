import os
import logging
from pathlib import Path

from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.format_util import FormatUtil
from bug_improving.utils.graph_util import GraphUtil
from bug_improving.utils.path_util import PathUtil
from config import DATA_DIR
import pandas as pd

if __name__ == "__main__":
    logging.warning("Loading bugs...")
    bugs = FileUtil.load_pickle(Path(DATA_DIR, "firefox_about_logins_bugs_with_step_object.json"))
    GraphUtil.get_index_cluster_dict(bugs)
    GraphUtil.get_steps(bugs)

    while True:
        # Clear the terminal:
        # Use the next line every time you wish to 'clear' the screen. Works with Windows and Linux.
        os.system('cls' if os.name == 'nt' else 'clear')

        choose = FormatUtil.format_bugkg_main_gui()
        search_input = None
        cluster_list = []
        bug_list = []
        if choose == FormatUtil.MAIN_CHOOSE_BY_ELEMENT:
            search_input = input("Please input the element: ")
            cluster_list = GraphUtil.find_clusters_by_element(search_input)
        elif choose == FormatUtil.MAIN_CHOOSE_BY_COSSIM:
            search_input = input("Please input the text: ")
            cluster_list = GraphUtil.find_clusters_by_cos(search_input)
        elif choose == FormatUtil.MAIN_CHOOSE_BY_CLUSTER_INDEX:
            search_input = input("Please input the cluster_index: ")
            cluster_list = [GraphUtil.INDEX_CLUSTER_DICT[int(search_input)]]
        elif choose == FormatUtil.MAIN_CHOOSE_BY_BUG_ID:
            search_input = input("Please input the bug id: ")
            bug_list = GraphUtil.find_relevant_ranked_bugs_by_bug_id(bugs, int(search_input))
        elif choose == FormatUtil.MAIN_CHOOSE_BY_EXIT:
            print("Bye~ ଘˊᵕˋଓ")
            break
        if cluster_list:
            if choose == 1:
                search_input = search_input + "_by_element"
            elif choose == 2:
                search_input = search_input + "_by_cos"
            print(f'Get {len(cluster_list)} cluster(s), please check. (•̤̀ᵕ•̤́๑)ᵒᵏ')
            # Create a Pandas Excel writer using XlsxWriter as the engine.
            writer = pd.ExcelWriter(PathUtil.get_search_result_filepath(search_input), engine='xlsxwriter')
            for index, cluster in enumerate(cluster_list):
                cluster_json = FormatUtil.format_cluster(cluster)
                df = pd.DataFrame(cluster_json)
                df.to_excel(writer, sheet_name=f"sheet_{index}", index=False, header=True)
                # Get the xlsxwriter objects from the dataframe writer object.
                # workbook = writer.book
                worksheet = writer.sheets[f"sheet_{index}"]
                # Set the column width.
                worksheet.set_column(0, 0, 50)
                # next_clusters = GraphUtil.get_next_clusters_by_bfs(cluster)
                # for next_cluster in next_clusters:
                #     if next_cluster != GraphUtil.LAYER:
                #         next_cluster = FormatUtil.format_cluster(next_cluster)
                #     print(next_cluster)
                # input()

            # Close the Pandas Excel writer and output the Excel file.
            writer.save()
        elif bug_list:
            writer = pd.ExcelWriter(PathUtil.get_search_result_filepath(search_input), engine='xlsxwriter')

            bug_list_json = FormatUtil.format_bug_list(bug_list)
            df = pd.DataFrame(bug_list_json)
            df.to_excel(writer, sheet_name=f"sheet_0", index=False, header=True)
            # Get the xlsxwriter objects from the dataframe writer object.
            # workbook = writer.book
            worksheet = writer.sheets[f"sheet_0"]
            # Set the column width.
            worksheet.set_column(0, 0, 50)

            # Close the Pandas Excel writer and output the Excel file.
            writer.save()
            print(f'Get {len(bug_list)} ranked bugs, please check. (•̤̀ᵕ•̤́๑)ᵒᵏ')
        else:
            print(f'Get {len(cluster_list)} cluster. ⚆_⚆')







