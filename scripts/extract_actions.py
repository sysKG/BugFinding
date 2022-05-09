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
                # print(step)
                step = SeedExtractor.replace_seed_by_placeholder(step)
                # print(step)
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
    Category.get_category_concept_dict(concept_category_dict)

    for category in Category.CATEGORY_CONCEPT_DICT.keys():
        print(f"{category}: {Category.CATEGORY_CONCEPT_DICT[category]}")
        # for concept in Category.CATEGORY_CONCEPT_DICT[category]:
        #     print(type(concept))
        #     input()

    # extract actions
    # print(SentUtil.NLP.pipe_names)
    # SentUtil.NLP.add_pipe("merge_noun_chunks")
    action_count_dict = dict()
    for bug in tqdm(bugs):
        if bug.description.steps_to_reproduce:
            for step in bug.description.steps_to_reproduce:
                step = NLPUtil.remove_serial_number(step)
                print("*************************************************")
                print(step)
                step = SeedExtractor.replace_seed_by_placeholder(step)
                print(step)
                if len(step) > 1024:
                    print("******************too long*******************************")
                    continue
                Action.categorize_actions_by_concept(step)
                # concept_category_pair_list = Category.extract_category(step)
    #             verb_adv_prt_prep_obj_concepts = Action.extract_action(step)
    #             verb = verb_adv_prt_prep_obj_concepts[0]
    #             adv = verb_adv_prt_prep_obj_concepts[1]
    #             prt = verb_adv_prt_prep_obj_concepts[2]
    #             prep = verb_adv_prt_prep_obj_concepts[3]
    #             obj = verb_adv_prt_prep_obj_concepts[4]
    #             concepts = verb_adv_prt_prep_obj_concepts[5]
    #             print("*************************************************")
    #             print(f"{verb}, {adv}, {prt}, {prep}, {obj}, {concepts}")
    #             print("*************************************************")
    #             if verb:
    #                 # action_count_dict[verb] = action_count_dict.get(verb, 0) + 1
    #                 action_count_dict[verb] = action_count_dict.get(verb, dict())
    #                 if adv:
    #                     action_count_dict[verb][adv] = action_count_dict[verb].get(adv, 0) + 1
    #                 elif prt:
    #                     action_count_dict[verb][prt] = action_count_dict[verb].get(prt, 0) + 1
    #                 elif prep:
    #                     action_count_dict[verb][prep] = action_count_dict[verb].get(prep, 0) + 1
    #                 else:
    #                     action_count_dict[verb]["count"] = action_count_dict[verb].get("count", 0) + 1
    #
    # for verb in action_count_dict.keys():
    #     # verb_count = action_count_dict[verb]["count"]
    #     print(f"{verb}:")
    #     for comp in action_count_dict[verb].keys():
    #         print(f"\t{comp}: {action_count_dict[verb][comp]}")
    for category in Category.CATEGORY_ACTION_DICT.keys():
        print(category)
        for action in Category.CATEGORY_ACTION_DICT[category].keys():
            print(f"\t{action}: {Category.CATEGORY_ACTION_DICT[category][action]}")
