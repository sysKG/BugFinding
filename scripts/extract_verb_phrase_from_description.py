import spacy

from bug_improving.types.product_component_pair import ProductComponentPair
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.nlp_util import NLPUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    nlp = spacy.load("en_core_web_sm", disable=["ner"])

    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_with_stp_filepath())
    # bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Firefox", "about:logins"))
    bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Toolkit", "Password Manager"))

    verb_phrase = []
    noun_phrase = []

    for bug in bugs:
        # if bug.id != 1243729:
        #     continue
        print(f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}")
        # print(bug.description)
        bug.description = bug.description.from_text(bug.description.text)
        # print(bug.description.prerequisites)
        # print("*********************************")
        # print(bug.description.steps_to_reproduce)
        try:
            for step in bug.description.steps_to_reproduce:
                # print(step)
                verb_phrase.extend(NLPUtil.extract_verb_phrase(nlp, step))
                noun_phrase.extend(NLPUtil.extract_noun_phrase(nlp, step))
        except:
            pass

    print(verb_phrase)
    print(noun_phrase)
    # print(bug.description.expected_results)
    # print("*********************************")
    # print(bug.description.actual_results)
    # input()
