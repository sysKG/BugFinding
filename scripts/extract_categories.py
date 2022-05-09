from tqdm import tqdm

from bug_improving.event_extraction.seed_extractor import SeedExtractor
from bug_improving.types.bug import Bugs
from bug_improving.types.entity import Category, Action
from bug_improving.types.product_component_pair import ProductComponentPair
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.nlp_util import NLPUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    # get dataset for extracting urls and seeds
    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_with_stp_filepath())
    one_bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Firefox", "about:logins"))
    two_bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Toolkit", "Password Manager"))
    one_bugs.bugs.extend(two_bugs.bugs)
    bugs = Bugs(one_bugs.bugs)

    text = ""
    for bug in tqdm(bugs, ascii=True):
        # text = text + "\n" + bug.description.text
        if bug.description.steps_to_reproduce:
            for step in bug.description.steps_to_reproduce:
                text = text + "\n" + step

    # extract urls and seeds and get placeholder
    urls = SeedExtractor.extract_urls(text)
    seeds = SeedExtractor.extract_seeds(text)
    SeedExtractor.get_placeholder_dict(seeds, urls)

    # extract categories
    concept_category_dict = dict()
    for bug in bugs:
        if bug.description.steps_to_reproduce:
            for step in bug.description.steps_to_reproduce:
                step = NLPUtil.remove_serial_number(step)
                print(step)
                step = SeedExtractor.replace_seed_by_placeholder(step)
                print(step)
                concept_category_pair_list = Category.extract_category(step)
                # concept_action_pair_list = Action.extract_action(step)

                if concept_category_pair_list:
                    for concept_category_pair in concept_category_pair_list:
                        concept = concept_category_pair[0]
                        category = concept_category_pair[1]
                        if concept is not None and category is not None:
                            # print(concept, category)
                            concept = SeedExtractor.PLACEHOLDER_SEED_DICT[concept]
                            concept_category_dict[concept] = concept_category_dict.get(concept, dict())
                            concept_category_dict[concept][category] = concept_category_dict[concept]. \
                                                                           get(category, 0) + 1

    print(len(seeds))
    print(seeds)
    print(len(concept_category_dict.keys()))
    print(concept_category_dict.keys())
    print(concept_category_dict)
    # get CATEGORY_CONCEPT_DICT
    category_concept_dict = Category.get_category_concept_dict(concept_category_dict)

    for category in category_concept_dict.keys():
        print(f"{category}: {category_concept_dict[category]}")

    # # get bugs to construct bug kg
    # bug_link_list = [1628401,
    #                  1572041,
    #                  1636909,
    #                  1572445
    #                  ]
    #
    # bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_filepath())
    # filtered_bugs = []
    # for bug in bugs:
    #     # print(bug.id)
    #     if bug.id in bug_link_list:
    #         filtered_bugs.append(bug)
    # filtered_bugs = Bugs(filtered_bugs)
    #
    # # exchange seed into placeholder
    # for bug in filtered_bugs:
    #     print(f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}")
    #     bug.description = bug.description.from_text(bug.description.text)
    #     print(bug.description.prerequisites)
    #     print("*********************************")
    #     print(bug.description.steps_to_reproduce)
    #     print("*********************************")
    #     print(bug.description.expected_results)
    #     print("*********************************")
    #     print(bug.description.actual_results)
    #     input()
