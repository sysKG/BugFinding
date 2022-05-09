import csv
from pathlib import Path

from bug_improving.types.product_component_pair import ProductComponentPair
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil
from config import DATA_DIR

if __name__ == "__main__":
    """
    need to choose
    """
    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_filepath())
    # bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_with_stp_filepath())
    # bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_without_stp_filepath())
    # print(bugs.get_length())
    """
    need to choose
    """
    pc = ProductComponentPair("Firefox", "about:logins")
    # pc = ProductComponentPair("Toolkit", "Password Manager")
    # pc = ProductComponentPair("Toolkit", "Password Manager: Site Compatibility")
    # pc = ProductComponentPair("Toolkit", "Form Autofill")

    # pc = ProductComponentPair("Toolkit", "Printing")
    # pc = ProductComponentPair("Core", "Print Preview")
    # pc = ProductComponentPair("Core", "Printing: Setup")

    # pc = ProductComponentPair("Firefox", "Theme")
    # pc = ProductComponentPair("Toolkit", "Themes")
    # pc = ProductComponentPair("WebExtensions", "Themes")

    # pc = ProductComponentPair("Core", "Plug-ins")
    # pc = ProductComponentPair("Firefox", "Preferences")
    # pc = ProductComponentPair("Firefox", "Firefox Accounts")

    # pc = ProductComponentPair("Toolkit", "Preferences")

    # pc = ProductComponentPair("Firefox", "Toolbars and Customization")

    pc_bugs = bugs.get_specified_product_component_bugs(pc)
    # for bug in pc_bugs:
    #     print(bug.summary)

    # print('Writing to file...\n')

    """
    need to choose
    """
    with open(PathUtil.get_specified_product_component_bug_filepath(pc), 'w') as file:
    # with open(PathUtil.get_specified_product_component_bug_with_stp_filepath(pc), 'w') as file:
    # with open(PathUtil.get_specified_product_component_bug_without_stp_filepath(pc), 'w') as file:
        writer = csv.writer(file)
        writer.writerow(("URL", "summary", "description"))

        for bug in pc_bugs:
            tp = (f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}", bug.summary, bug.description)
            writer.writerow(tp)
    # print('Written to file.\n')
