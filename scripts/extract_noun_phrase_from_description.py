import spacy

from bug_improving.types.product_component_pair import ProductComponentPair
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.nlp_util import NLPUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    """
    get all the noun phrases, including nested phrases
    https://stackoverflow.com/questions/48925328/how-to-get-all-noun-phrases-in-spacy
    """

    nlp = spacy.load("en_core_web_sm", disable=["ner"])

    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_with_stp_filepath())
    bugs = bugs.get_specified_product_component_bugs(ProductComponentPair("Toolkit", "Password Manager"))
    text = "First set a Master Password in Options -> Privacy & Security -> Check Use a master password -> set Master password."
    nounp = NLPUtil.extract_noun_phrase(nlp, text)
    print(spacy.explain("conj"))
    print(nounp)
    for bug in bugs:
        print(f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}")
        print(bug.description)
        # sentences = [i for i in nlp(bug.description).sents]  #
        for sentence in nlp(bug.description).sents:
            print(sentence.text)
            noun_phrase = []
            for base_noun in sentence.noun_chunks:
                # print(base_noun)
                # get base noun phrases
                noun_phrase.append(base_noun.text)
                nested_noun = sentence[base_noun.root.left_edge.i: base_noun.root.right_edge.i + 1]
                if nested_noun.text != base_noun.text:
                    # print(nested_noun)
                    # get nested noun phrases
                    noun_phrase.append(nested_noun.text)
            print(noun_phrase)
        input()
