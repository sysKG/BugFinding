from tqdm import tqdm

from bug_improving.event_extraction.seed_extractor import SeedExtractor
from bug_improving.types.product_component_pair import ProductComponentPair
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.nlp_util import NLPUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    # bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_filepath())
    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_with_stp_filepath())
    bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Firefox", "about:logins"))
    # bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Toolkit", "Password Manager"))
    # bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Toolkit", "Form Autofill"))
    # bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Firefox", "Security"))

    # seeds = set()
    seed_count_dict = dict()

    for bug in tqdm(bugs, ascii=True):
        # print(f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}")
        # print(bug.description)
        # print("****************")
        # if bug.id != 1597651 and bug.id != 1613932 and bug.id != 990455:
        # print(bug.description.text)

        bug.description.text = NLPUtil.replace_url_by_placeholder(bug.description.text)
        # print("OK")
        # else:
        #     print(bug.description.text)
        # seeds = seeds | SeedExtractor.extract_seeds_by_regex(bug.description.text)
        seed_count_dict = SeedExtractor.extract_seeds_by_regex(bug.description.text, seed_count_dict)

    seed_count_dict = SeedExtractor.filter_seeds_by_count(seed_count_dict)
    seed_count_dict = sorted(seed_count_dict.items(), key=lambda i: (i[1]), reverse=True)
    # seed_count_dict = sorted(seed_count_dict.values(), reverse=True)
    # print(seed_count_dict)
    for seed in seed_count_dict:
        # print(f"{seed}: {seed_count_dict[seed]}")
        print(f"{seed}")

    # for seed in seeds:
    #     print(seed)
    # print(seeds)
