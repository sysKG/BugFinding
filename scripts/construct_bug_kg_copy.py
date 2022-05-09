"""
https://www.sbert.net/examples/applications/paraphrase-mining/README.html
"""
import logging
from pathlib import Path

from bug_improving.event_extraction.seed_extractor import SeedExtractor
from bug_improving.types.element import Element
from bug_improving.types.entity import Category
from bug_improving.types.product_component_pair import ProductComponentPair
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.list_util import ListUtil
from bug_improving.utils.nlp_util import NLPUtil
from bug_improving.utils.path_util import PathUtil
from config import DATA_DIR

if __name__ == "__main__":

    model = NLPUtil.SENTENCE_TRANSFORMER

    # get dataset for extracting urls and seeds
    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_with_stp_filepath())
    # print(bugs.get_length())
    # print(bugs.overall_bugs())
    # bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Firefox", "Preferences"))
    bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Firefox", "about:logins"))

    # extract urls and seeds and get placeholder
    logging.warning("Extract URLs...")
    urls = SeedExtractor.extract_urls_from_bugs(bugs)
    logging.warning("Extract Seeds from bugs...")
    seeds_from_bugs = SeedExtractor.extract_seeds_from_bugs(bugs)
    # seeds = seeds_from_bugs
    logging.warning("Extract Seeds from ftl...")
    # component = "about_preferences"
    # ftl_filename = "preferences_ftl.json"
    # html_filename = "preferences_from_scrape_url.xhtml"
    component = "about_logins"
    ftl_filename = "aboutLogins_ftl.json"
    html_filename = "aboutLogins.html"
    category_element_dict = Element.get_category_element_dict(component, ftl_filename, html_filename)
    seeds = set(ListUtil.convert_nested_list_to_flatten_list(category_element_dict.values()))
    seeds = seeds | seeds_from_bugs

    # for category, element_list in category_element_dict.items():
    #     print(category)
    #     print(f"\t{element_list}")
    #     seeds.extend(element_list)
    # seeds = category_element_dict.values()
    logging.warning("Get SeedExtractor.PLACEHOLDER_DICT...")
    SeedExtractor.get_placeholder_dict(seeds, urls)
    for key, value in SeedExtractor.PLACEHOLDER_SEED_DICT.items():
        print(f"{key}: {value}")

    # split sections in description into atomic_steps
    logging.warning("Split steps_to_reproduce into atomic_steps...")
    bugs.extract_steps()

    # extract categories from bugs
    logging.warning("Extract categories for concepts from bugs...")
    category_concept_dict = bugs.extract_categories()
    # print(category_concept_dict)

    # categories, concepts = Category.get_static_part(category_element_dict)
    # for category in categories:
    #     print(category)

    logging.warning("Merging elements from ftl and concepts from bugs...")
    categories, concepts, actions = Category.get_static_part(category_element_dict,
                                                             category_concept_dict)

    for category in categories:
        print(category)

    logging.warning("Transform steps into objects...")
    # concepts = Concepts(categories.get_concepts())
    bugs.transform_sections_into_objects(concepts)
    # FileUtil.dump_pickle(Path(DATA_DIR, "firefox_about_logins_bugs_with_step_object.json"), bugs)
    #
    # bugs = FileUtil.load_pickle(Path(DATA_DIR, "firefox_about_logins_bugs_with_step_object.json"))

    bugs.merge_steps_by_paraphrase_mining(model)

    for bug in bugs:
        if bug.description.steps_to_reproduce:
            for step in bug.description.steps_to_reproduce:
                print(step)
    # FileUtil.dump_pickle(Path(DATA_DIR, "firefox_preferences_bugs_with_step_object.json"), bugs)
    FileUtil.dump_pickle(Path(DATA_DIR, "firefox_about_logins_bugs_with_step_object.json"), bugs)

