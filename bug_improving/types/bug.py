import logging
from datetime import datetime
from pathlib import Path

import numpy
import sentence_transformers
from sentence_transformers import util
from tqdm import tqdm

from bug_improving.event_extraction.seed_extractor import SeedExtractor
from bug_improving.types.attachment import Attachment
from bug_improving.types.description import Description, Step, Section
from bug_improving.types.entity import Category
from bug_improving.types.product_component_pair import ProductComponentPair, ProductComponentPairFramework
from bug_improving.types.tossing_path import TossingPath, TossingPathFramework
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.list_util import ListUtil
from bug_improving.utils.nlp_util import NLPUtil, SentUtil
from config import STEP_MERGE_THRESHOLD, STEP_MAX_TOKEN_NUM, MAX_STEP_NUM, ELEMENT_MERGE_THRESHOLD, \
    ACTION_MERGE_THRESHOLD, SPACY_BATCH_SIZE, SBERT_BATCH_SIZE, DATA_DIR
import numpy as np


class Bug:

    def __init__(self, id=None, summary=None, description=None, product_component_pair=None, tossing_path=None,
                 creation_time=None, closed_time=None, last_change_time=None, status=None, attachments=None):
        self.id = id
        self.summary = summary
        self.description = description
        self.product_component_pair = product_component_pair
        self.tossing_path = tossing_path
        self.creation_time = creation_time
        self.closed_time = closed_time
        self.last_change_time = last_change_time
        self.status = status
        self.attachments = attachments
        # self.events = list()

    def __repr__(self):
        return f'https://bugzilla.mozilla.org/show_bug.cgi?id={self.id} - {self.summary} - ' \
               f'{self.product_component_pair} - {self.tossing_path} - {self.creation_time} - ' \
               f'{self.closed_time} - {self.last_change_time} - {self.attachments}'

    def __str__(self):
        return f'https://bugzilla.mozilla.org/show_bug.cgi?id={self.id} - {self.summary} - ' \
               f'{self.product_component_pair} - {self.tossing_path} - {self.creation_time} - ' \
               f'{self.closed_time} - {self.last_change_time} - {self.attachments}'

    @staticmethod
    def from_dict(bug_dict):
        """
        get bugs from bugzilla
        :param bug_dict:
        :return:
        """
        bug = Bug()
        bug.id = bug_dict['id']
        bug.summary = bug_dict['summary']
        try:
            bug.description = Description.from_text(bug_dict['comments'][0]['text'])
        except:
            pass
        bug.product_component_pair = ProductComponentPair(bug_dict['product'], bug_dict['component'])
        bug.tossing_path = TossingPath(Bug.get_tossing_path(bug_dict['history'], bug.product_component_pair))

        datetime_format = "%Y-%m-%dT%H:%M:%SZ"
        # datetime_format = "%Y-%m-%d %H:%M:%S"
        bug.creation_time = datetime.strptime(bug_dict['creation_time'], datetime_format)
        # if bug_dict['cf_last_resolved'] is not None:
        if 'cf_last_resolved' in bug_dict.keys():
            if bug_dict['cf_last_resolved']:
                bug.closed_time = datetime.strptime(bug_dict['cf_last_resolved'], datetime_format)
        bug.last_change_time = datetime.strptime(bug_dict['last_change_time'], datetime_format)

        # bug.creation_time = dateutil.parser.parse(bug_dict['creation_time'])
        # if 'cf_last_resolved' in bug_dict.keys():
        #     bug.closed_time = dateutil.parser.parse(bug_dict['cf_last_resolved'])
        # bug.last_change_time = dateutil.parser.parse(bug_dict['last_change_time'])

        bug.status = bug_dict['status']
        bug.attachments = Bug.get_attachments(bug_dict['attachments'])

        # bug.summary_token = NLPUtil.preprocess(bug.summary)
        # bug.description_token = NLPUtil.preprocess(bug.description)
        return bug

    @staticmethod
    def from_dict_github(bug_dict):
        """
        get bugs from GitHub's issues
        :param bug_dict:
        :return:
        """
        bug = Bug()
        bug.id = bug_dict['url']
        bug.summary = bug_dict['title']
        try:
            bug.description = Description.from_text(bug_dict['body'])
        except:
            pass
        # bug.product_component_pair = ProductComponentPair(bug_dict['product'], bug_dict['component'])
        # bug.tossing_path = TossingPath(Bug.get_tossing_path(bug_dict['history'], bug.product_component_pair))
        bug.creation_time = datetime.strptime(bug_dict['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        if bug_dict['closed_at'] is not None:
            bug.closed_time = datetime.strptime(bug_dict['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
        bug.last_change_time = datetime.strptime(bug_dict['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
        bug.status = bug_dict['state']

        # bug.summary_token = NLPUtil.preprocess(bug.summary)
        # bug.description_token = NLPUtil.preprocess(bug.description)
        return bug

    @staticmethod
    def get_attachments(attachments):
        attachment_list = []
        for attachment in attachments:
            attachment_list.append(Attachment(attachment['id'], attachment['bug_id'], attachment['summary'],
                                              attachment['description'], attachment['file_name'],
                                              attachment['content_type']))
        return attachment_list

    @staticmethod
    def get_tossing_path(history, last_product_component_pair):
        tossing_path = []
        is_tossing = 0
        for one in history:
            product_component_pair = ProductComponentPair()
            for change in one['changes']:
                if change['field_name'] == 'product':
                    product_component_pair.product = change['removed']
                    is_tossing = 1
                if change['field_name'] == 'component':
                    product_component_pair.component = change['removed']
                    is_tossing = 1
            if is_tossing == 1 and \
                    (product_component_pair.product is not None or product_component_pair.component is not None):
                tossing_path.append(product_component_pair)
        tossing_path.append(last_product_component_pair)
        tossing_path = Bug.complete_tossing_path(tossing_path)

        return tossing_path

    @staticmethod
    def complete_tossing_path(tossing_path):
        n = len(tossing_path)
        i = 0
        for pair in reversed(tossing_path):
            if pair.product is None:
                tossing_path[n - i - 1].product = tossing_path[n - i].product
            if pair.component is None:
                tossing_path[n - i - 1].component = tossing_path[n - i].component
            i = i + 1
        return tossing_path

    def transform_steps_into_objects(self, concepts):
        """
        transform step (string) into step (object)
        @param concepts:
        @type concepts:
        @return:
        @rtype:
        """
        # print(bug)
        if self.description.steps_to_reproduce:
            # can get out
            # concepts = Concepts(categories.get_concepts())
            # print(bug.description.steps_to_reproduce)
            # print(type(bug.description.steps_to_reproduce))
            for index, step in enumerate(self.description.steps_to_reproduce):
                # print(step)
                prev_step = None
                if index != 0:
                    prev_step = self.description.steps_to_reproduce[index - 1]
                    self.description.steps_to_reproduce[index] = Step.from_step(f"{index}", self, step,
                                                                                concepts, prev_step)
                    self.description.steps_to_reproduce[index - 1].next_step = self.description.steps_to_reproduce[
                        index]
                else:
                    self.description.steps_to_reproduce[index] = Step.from_step(f"{index}", self, step,
                                                                                concepts, prev_step)
                # print(type(self.description.steps_to_reproduce[index]))


class Bugs:
    def __init__(self, bugs=None, product_component_pair_framework_list=None):
        self.bugs = bugs
        self.product_component_pair_framework_list = product_component_pair_framework_list
        self.step_index_cluster_dict = None  # dict{ key: index,
        # value: cluster ((set(step(object), step(object), ...))})

        # self.categories = None
        # self.concepts = None
        # self.length = len(bugs)

    def __iter__(self):
        for bug in self.bugs:
            yield bug

    def get_length(self):
        return len(self.bugs)

    def count_tossing_bugs(self):
        """
        count tossing bugs
        :return: the number of tossing bugs
        """
        count = 0
        for bug in self:
            if bug.tossing_path.length > 1:
                count = count + 1
        return count

    def get_specified_product_component_bugs(self, product_component_pair):
        """
        get specified product&component's bugs from bugs
        :param product_component_pair: specified product&component
        :return: specified product&component's bugs
        """
        specified_bugs = []
        for bug in self.bugs:
            if bug.product_component_pair == product_component_pair:
                specified_bugs.append(bug)
        return Bugs(specified_bugs)
        # return specified_bugs

    def classify_bugs_by_product_component_pair_list(self, product_component_pair_list):
        """
        使用product&component_pair_list将bugs分类
        :param product_component_pair_list:
        :return: product_component_pair - bugs dict
        """
        pc_bugs_dict = dict()
        for pc in product_component_pair_list:
            pc_bugs_dict[pc] = self.get_specified_product_component_bugs(pc)

        return pc_bugs_dict

    def get_pc_mistossed_bug_num(self, product_component_pair_list):
        """
        get pc: mistossed bug num dict
        mistossed bug: tossed out bugs
        :param product_component_pair_list:
        :return: pc: mistossed bug num dict
        """
        pc_mistossed_bug_num = dict()
        for bug in self.bugs:
            # print(f'https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}')
            for pc in bug.tossing_path.product_component_pair_list:
                if pc in product_component_pair_list and pc != bug.product_component_pair:
                    pc_mistossed_bug_num[f"{pc.product}::{pc.component}"] = pc_mistossed_bug_num.get(
                        f"{pc.product}::{pc.component}", 0) + 1

        for pc in product_component_pair_list:
            if f"{pc.product}::{pc.component}" not in pc_mistossed_bug_num.keys():
                pc_mistossed_bug_num[f"{pc.product}::{pc.component}"] = pc_mistossed_bug_num.get(
                    f"{pc.product}::{pc.component}", 0)
        return pc_mistossed_bug_num

    def get_pc_mistossed_bug_dict(self, product_component_pair_list):
        """
        get pc: mistossed bugs dict
        mistossed bug: tossed out bugs
        :param product_component_pair_list:
        :return: pc: mistossed bugs dict
        """
        pc_mistossed_bug_dict = dict()
        for bug in self.bugs:
            # print(f'https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}')
            for pc in bug.tossing_path.product_component_pair_list:
                if pc in product_component_pair_list and pc != bug.product_component_pair:
                    temp = pc_mistossed_bug_dict.get(pc, list())
                    temp.append(bug)
                    pc_mistossed_bug_dict[pc] = temp
            # print(pc_mistossed_bug_dict)
            # input()
        for pc in product_component_pair_list:
            if pc not in pc_mistossed_bug_dict.keys():
                temp = pc_mistossed_bug_dict.get(pc, list())
                pc_mistossed_bug_dict[pc] = temp
        return pc_mistossed_bug_dict

    def overall_bugs(self):
        """
        统计bugs中每个product&component包含的bug个数、tossing bug个数 及 tossing path数
        :return:
        """
        p_c_pair_list = []
        p_c_pair_framework_list = []

        for bug in self.bugs:
            # bug = Bug.dict_to_object(bug)
            if bug.product_component_pair not in p_c_pair_list:
                p_c_pair_list.append(bug.product_component_pair)

                p_c_pair_framework = ProductComponentPairFramework()
                p_c_pair_framework.product_component_pair = bug.product_component_pair
                p_c_pair_framework.bug_nums = 1

                p_c_pair_framework.tossing_path_framework_list = []
                tossing_path_framework = TossingPathFramework()
                tossing_path_framework.tossing_path = bug.tossing_path
                tossing_path_framework.nums = 1
                tossing_path_framework.bug_id_list = []
                tossing_path_framework.bug_id_list.append(bug.id)
                p_c_pair_framework.tossing_path_framework_list.append(tossing_path_framework)
                p_c_pair_framework_list.append(p_c_pair_framework)
            else:
                for framework in p_c_pair_framework_list:
                    if bug.product_component_pair == framework.product_component_pair:
                        framework.bug_nums = framework.bug_nums + 1
                        i = 0
                        for tossing_path_framework in framework.tossing_path_framework_list:
                            if tossing_path_framework.tossing_path == bug.tossing_path:
                                tossing_path_framework.bug_id_list.append(bug.id)
                                tossing_path_framework.nums = tossing_path_framework.nums + 1
                                break
                            i = i + 1
                        if i == len(framework.tossing_path_framework_list):
                            tossing_path_framework = TossingPathFramework()
                            tossing_path_framework.tossing_path = bug.tossing_path
                            tossing_path_framework.bug_id_list = []
                            tossing_path_framework.bug_id_list.append(bug.id)
                            tossing_path_framework.nums = 1
                            framework.tossing_path_framework_list.append(tossing_path_framework)
                        break
        sum = 0
        sum_tossing = 0
        sum_tossing_path = 0
        for p_c_pair_framework in p_c_pair_framework_list:
            p_c_pair_framework.get_tossing_bug_nums()
            sum = sum + p_c_pair_framework.bug_nums
            sum_tossing = sum_tossing + p_c_pair_framework.tossing_bug_nums
            sum_tossing_path = sum_tossing_path + len(p_c_pair_framework.tossing_path_framework_list)
        # overall
        print(f'bug_nums: {sum}')
        print(f'tossing_bug_nums: {sum_tossing}')  # tossing bug nums
        print(f'tossing_path_nums: {sum_tossing_path}')  # tossing path nums
        print(f'product_component_nums: {len(p_c_pair_framework_list)}')
        for p_c_pair_framework in p_c_pair_framework_list:
            print(p_c_pair_framework.product_component_pair)
            # each of p&c
            print(f'bug_nums: {p_c_pair_framework.bug_nums}')
            print(f'tossing_bug_nums: {p_c_pair_framework.tossing_bug_nums}')
            print(f'tossing_path_nums: {len(p_c_pair_framework.tossing_path_framework_list)}')
        self.product_component_pair_framework_list = p_c_pair_framework_list
        # print(self.product_component_pair_framework_list)

    # def find_bugs_by_bug_id(self, bug_id):
    #     for bug in self.bugs:
    #         if bug.id == bug_id:
    #             return bug

    def get_bug_summary_list(self):
        """
        get bugs' summary
        :return: bug summary list
        """
        summary_list = []
        for bug in self.bugs:
            id_summary = {"id": f'https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}',
                          "summary": bug.summary}
            summary_list.append(id_summary)
        return summary_list

    def split_steps_to_reproduce_into_steps(self):
        """
        split steps_to_reproduce section into steps (when steps_to_reproduce is still string)
        @return:
        @rtype:
        """
        steps_to_reproduce_list = []
        for bug in tqdm(self.bugs):
            steps_to_reproduce_list.append(bug.description.steps_to_reproduce)
        logging.warning(f"{len(steps_to_reproduce_list)} steps_to_reproduces into sents")
        sent_steps_to_reproduce_list = NLPUtil.sentence_tokenize_by_spacy_batch(steps_to_reproduce_list)
        for index, sent_steps_to_reproduce in enumerate(tqdm(sent_steps_to_reproduce_list)):
            self.bugs[index].description.steps_to_reproduce = sent_steps_to_reproduce

    def filter_bugs_by_step(self):
        """
        filter bugs by step
        1. remove step's serial number
        2. remove step which only has non_alphanumeric
        3. remove bug that has steps with more than STEP_MAX_TOKEN_NUM tokens
        4. remove bug that has more than MAX_STEP_NUM steps
        @return: filtered_bugs
        @rtype: Bugs()
        """
        filtered_bugs = list()
        for bug in tqdm(self.bugs, ascii=True):
            steps_to_reproduce = list()
            for step_lines in bug.description.steps_to_reproduce:
                steps = step_lines.splitlines()
                for step in steps:
                    step = NLPUtil.remove_serial_number(step)
                    # if not NLPUtil.is_non_alphanumeric(step):
                    if not NLPUtil.is_non_alpha(step):
                        if len(step.split()) > STEP_MAX_TOKEN_NUM:  # if step has too much tokens,
                            # then steps to reproduce maybe consist of one paraphrase
                            # print(step)
                            steps_to_reproduce = list()
                            break
                        steps_to_reproduce.append(step)

            if 0 < len(steps_to_reproduce) <= MAX_STEP_NUM:
                bug.description.steps_to_reproduce = steps_to_reproduce
                filtered_bugs.append(bug)
        return Bugs(filtered_bugs)

    def sort_by_creation_time(self):
        self.bugs = sorted(self.bugs, key=lambda x: x.creation_time, reverse=False)

    def split_dataset_by_creation_time(self, creation_time):
        """
        sort bugs by creation time
        split bugs into
            80% training dataset
            20% testing dataset
        :return:
        """
        # self.sort_by_creation_time()
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"
        # datetime_format = "%Y-%m-%d %H:%M:%S"
        creation_time = datetime.strptime(creation_time, datetime_format)

        train_bugs = list()
        test_bugs = list()
        for bug in self.bugs:
            if bug.creation_time < creation_time:
                train_bugs.append(bug)
            else:
                test_bugs.append(bug)

        train_bugs = Bugs(train_bugs)
        # train_bugs.overall_bugs()
        test_bugs = Bugs(test_bugs)
        # test_bugs.overall_bugs()
        return train_bugs, test_bugs

    def split_dataset_by_tossed_and_untossed(self):
        """
        :return:
        """
        tossed_bugs = list()
        untossed_bugs = list()
        for bug in self.bugs:
            if bug.tossing_path.length > 1:
                tossed_bugs.append(bug)
            else:
                untossed_bugs.append(bug)
        tossed_bugs = Bugs(tossed_bugs)
        untossed_bugs = Bugs(untossed_bugs)
        return tossed_bugs, untossed_bugs

    def split_dataset_by_pc(self, product_component_pair_list):
        """
        split bugs according to pc, for each pc: 80% training dataset & 20% testing dataset
        :param product_component_pair_list:
        :return:
        """
        train_bugs = list()
        test_bugs = list()

        for pc in product_component_pair_list:
            bugs = self.get_specified_product_component_bugs(pc)
            train_bugs.extend(list(bugs)[0: int(bugs.get_length() * 0.8)])
            test_bugs.extend(list(bugs)[int(bugs.get_length() * 0.8): bugs.get_length()])
        train_bugs = Bugs(train_bugs)
        # train_bugs.overall_bugs()
        test_bugs = Bugs(test_bugs)
        # test_bugs.overall_bugs()
        return train_bugs, test_bugs

    def split_dataset_by_pc_and_creation_time(self, product_component_pair_list):
        """
        sort bugs by creation time
        split bugs according to pc, for each pc: 80% training dataset & 20% testing dataset
        :param product_component_pair_list:
        :return:
        """
        self.sort_by_creation_time()

        train_bugs = list()
        test_bugs = list()

        for pc in product_component_pair_list:
            bugs = self.get_specified_product_component_bugs(pc)
            train_bugs.extend(list(bugs)[0: int(bugs.get_length() * 0.8)])
            test_bugs.extend(list(bugs)[int(bugs.get_length() * 0.8): bugs.get_length()])
        train_bugs = Bugs(train_bugs)
        # train_bugs.overall_bugs()
        test_bugs = Bugs(test_bugs)
        # test_bugs.overall_bugs()
        return train_bugs, test_bugs

    def get_nodes_edges_for_bug_kg(self):

        node_set = set()
        edge_set = set()

        for bug in self.bugs:
            for index, step in enumerate(bug.description.steps_to_reproduce):
                node_set.add(step)
                # node_set.add(step.action_object_condition_tuple[0])
                if index + 1 < len(bug.description.steps_to_reproduce):
                    edge_set.add((step, bug.description.steps_to_reproduce[index + 1]))

        return node_set, edge_set

    # def extract_steps(self):
    #     """
    #     split sections in description into atomic_steps
    #     @param bugs:
    #     @type bugs:
    #     @return:
    #     @rtype:
    #     """
    #     for bug in tqdm(self.bugs):
    #         # print(bug)
    #         # if bug.description.prerequisites:
    #         #     bug.description.prerequisites = Description.extract_steps(bug.description.prerequisites)
    #         if bug.description.steps_to_reproduce:
    #             # if len(bug.description.steps_to_reproduce) <= 512:
    #             # try:
    #             bug.description.steps_to_reproduce = Description.extract_steps(bug.description.steps_to_reproduce)
    #             # except Exception:
    #             #     print(bug.id)
    #             # else:
    #             #     bug.description.steps_to_reproduce = [bug.description.steps_to_reproduce]
    #         # if bug.description.actual_results:
    #         #     bug.description.actual_results = Description.extract_steps(bug.description.actual_results)
    #         # if bug.description.expected_results:
    #         #     bug.description.expected_results = Description.extract_steps(bug.description.expected_results)
    #
    #         # if bug.description.notes:
    #         #     bug.description.notes = Description.extract_steps(bug.description.notes)

    def get_steps_list(self):
        """
        get all steps in bugs
        @return: [step (str), step, ...]
        @rtype: list
        """
        steps = []
        for bug in tqdm(self.bugs, ascii=True):
            for step in bug.description.steps_to_reproduce:
                steps.append(step)
        return steps

    def replace_by_placeholder(self):
        """
        NLPUtil.remove_text_between_parenthesis(step)
        SeedExtractor.replace_seed_by_placeholder(step)
        @return:
        @rtype:
        @todo: step = NLPUtil.remove_text_between_parenthesis(step) can make step = "", and still in steps to reproduce
               solutions: 1. put step = NLPUtil.remove_text_between_parenthesis(step) ahead -> is much better
                          2. add if step: step = SeedExtractor.replace_seed_by_placeholder(step)
                                          # print(step)
                                          steps_to_reproduce.append(step)
        """
        # sorting dictionary by length of values from long to short,
        # if not, create new login will be replaced by new login
        # placeholders = sorted(SeedExtractor.PLACEHOLDER_SEED_DICT, key=lambda k: len(SeedExtractor.PLACEHOLDER_SEED_DICT[k]),
        #                       reverse=True)
        for bug in tqdm(self.bugs, ascii=True):
            if bug.description.steps_to_reproduce:
                steps_to_reproduce = []
                for step in bug.description.steps_to_reproduce:
                    # print(step)
                    step = NLPUtil.remove_text_between_parenthesis(step)
                    step = SeedExtractor.replace_seed_by_placeholder(step)
                    # print(step)
                    steps_to_reproduce.append(step)
                bug.description.steps_to_reproduce = steps_to_reproduce

    def extract_steps(self):
        """
        split sections in description into atomic_steps
        @param bugs:
        @type bugs:
        @return:
        @rtype:
        """
        logging.warning("get all steps in bugs")
        SentUtil.SENT_LIST = self.get_steps_list()
        SentUtil.get_sent_has_cconj_list(SentUtil.SENT_LIST)
        NLPUtil.SPACY_NLP.enable_pipe("benepar")
        NLPUtil.SPACY_NLP.enable_pipe("merge_noun_chunks")
        logging.warning(NLPUtil.SPACY_NLP.pipe_names)
        # logging.warning(len(SentUtil.SENT_LIST))
        # logging.warning(len(SentUtil.SENT_HAS_CCONJ_LIST))
        # SentUtil.get_sent_cons_doc_list(SentUtil.SENT_LIST)
        # logging.warning(len(SentUtil.SENT_LIST))
        # logging.warning(len(SentUtil.SENT_HAS_CCONJ_LIST))
        # logging.warning(len(SentUtil.SENT_CONS_DOC_LIST))

        logging.warning("Split steps into atomic steps...")
        for bug in tqdm(self.bugs):
            # print(bug)
            # if bug.description.prerequisites:
            #     bug.description.prerequisites = Description.extract_steps(bug.description.prerequisites)
            if bug.description.steps_to_reproduce:
                # if len(bug.description.steps_to_reproduce) <= 512:
                # try:
                bug.description.steps_to_reproduce = Description.extract_steps(bug.description.steps_to_reproduce)
                # except Exception:
                #     print(bug.id)
                # else:
                #     bug.description.steps_to_reproduce = [bug.description.steps_to_reproduce]
            # if bug.description.actual_results:
            #     bug.description.actual_results = Description.extract_steps(bug.description.actual_results)
            # if bug.description.expected_results:
            #     bug.description.expected_results = Description.extract_steps(bug.description.expected_results)

            # if bug.description.notes:
            #     bug.description.notes = Description.extract_steps(bug.description.notes)

    def transform_sections_into_objects(self, concepts, actions):
        """
        transform step (string) into step (object)
        @return:
        @rtype:
        """
        # logging.warning("replace urls and concepts by placeholder for steps")
        # self.replace_by_placeholder()
        # logging.warning("get all steps in bugs")
        # SentUtil.SENT_LIST = self.get_steps_list()
        # logging.warning("SpaCy NLP for pos ...")
        NLPUtil.SPACY_NLP.enable_pipe("merge_noun_chunks")
        NLPUtil.SPACY_NLP.disable_pipes("benepar")
        # docs = NLPUtil.SPACY_NLP.pipe(SentUtil.SENT_LIST, batch_size=SPACY_BATCH_SIZE,
        #                               disable=["benepar"])
        # docs = list(docs)
        # # logging.warning(SpacyModel.NLP.pipe_names)
        # # concept_embedding = NLPUtil.SENTENCE_TRANSFORMER(concepts.concept_name_list)
        # logging.warning("transform step (string) into step (object)...")
        # doc_index = 0
        for bug in tqdm(self.bugs):
            #     # transform step (step) into Step object
            #     # if bug.description.steps_to_reproduce:
            #     for index, step in enumerate(bug.description.steps_to_reproduce):
            #         # print(step)
            #         prev_step = None
            #         if index != 0:
            #             prev_step = bug.description.steps_to_reproduce[index - 1]
            #             bug.description.steps_to_reproduce[index] = Step.from_step(f"{index}", bug, step,
            #                                                                        concepts, prev_step, docs[doc_index])
            #             bug.description.steps_to_reproduce[index - 1].next_step = bug.description.steps_to_reproduce[index]
            #         else:
            #             bug.description.steps_to_reproduce[index] = Step.from_step(f"{index}", bug, step,
            #                                                                        concepts, prev_step, docs[doc_index])
            #         doc_index = doc_index + 1
            bug.transform_steps_into_objects(concepts)
            if bug.description.prerequisites:
                bug.description.prerequisites = Section.from_section(bug.description.prerequisites, concepts)
            if bug.description.expected_results:
                bug.description.expected_results = Section.from_section(bug.description.expected_results, concepts)
            if bug.description.actual_results:
                bug.description.actual_results = Section.from_section(bug.description.actual_results, concepts)
            if bug.description.notes:
                bug.description.notes = Section.from_section(bug.description.notes, concepts)

        step_list, target_list, action_list = self.get_step_target_action_list()
        logging.warning("Extract concepts from step targets...")
        self.extract_concept_from_step_target(concepts, target_list, step_list)
        logging.warning("Match action_object from step action...")
        self.match_action_into_object(actions, action_list, step_list)

    def get_step_target_action_list(self):
        step_list = list()
        target_list = list()
        action_list = list()
        for bug in tqdm(self.bugs, ascii=True):
            for step in bug.description.steps_to_reproduce:
                if not step.target:
                    step.target = ""
                target_list.append(step.target)
                if not step.action:
                    step.action = ""
                action_list.append(step.action)

                step_list.append(step)
        return step_list, target_list, action_list

    def extract_concept_from_step_target(self, concepts, target_list, step_list):
        """
        Extract concept from target in step, calculate the cossim (target, concept)
        if >= ELEMENT_MERGE_THRESHOLD
        add concept into step.concepts and step.concepts_in_target
        @todo: concepts from Placeholder and concepts from cossom confliction, e.g., Enter the Primary Password.
                    {1758 - Password - Text - None - None, 83 - Use a Primary Password - Checkbox - None - None}
        @param concepts:
        @type concepts: [Concept, Concept, ...]
        @return:
        @rtype:
        """
        # step_list = list()
        # target_list = list()
        # for bug in tqdm(self.bugs, ascii=True):
        #     for step in bug.description.steps_to_reproduce:
        #         if not step.target:
        #             step.target = ""
        #         target_list.append(step.target)
        #         step_list.append(step)

        target_embeddings = NLPUtil.SBERT_MODEL.encode(target_list)
        concepts.get_concept_name_embedding_list()
        # concept_embedding = NLPUtil.SENTENCE_TRANSFORMER(concepts.concept_name_list)
        pairs_list = sentence_transformers.util.semantic_search(target_embeddings,
                                                                concepts.concept_name_embedding_list,
                                                                top_k=1)
        # pairs_list = NLPUtil.get_pairs_with_cossim_by_decreasing(target_embeddings,
        #                                                          concepts.concept_name_embedding_list)
        # top_1_pairs = NLPUtil.get_top_1_pairs_with_cossim(pairs_list)
        for index, top_1_pair in tqdm(enumerate(pairs_list), ascii=True):

            if top_1_pair[0]['score'] >= ELEMENT_MERGE_THRESHOLD:
                concept_index = top_1_pair[0]['corpus_id']
                concept_in_target = concepts.find_concept_by_name(concepts.concept_name_list[concept_index])
                step_list[index].concepts.add(concept_in_target)
                step_list[index].concepts_in_target.add(concept_in_target)

    def match_action_into_object(self, actions, action_list, step_list):
        """
        match action with action_object

        @param actions:
        @type actions:
        @param action_list:
        @type action_list:
        @param step_list:
        @type step_list:
        @return:
        @rtype:
        """
        action_embeddings = NLPUtil.SBERT_MODEL.encode(action_list)
        action_object_equivalent_names = list()
        index_action_object_dict = dict()
        index = 0
        for action in actions:
            for equivalent_name in action.equivalent:
                action_object_equivalent_names.append(equivalent_name)
                index_action_object_dict[index] = index_action_object_dict.get(index, action)
                index = index + 1
            # action_object_equivalent_embeddings.append(action.equivalent_embedding)
        # flatten_action_object_equivalent_embeddings = ListUtil.convert_flatten_list_to_nested_list_by_value\
        #     (action_object_equivalent_embeddings)
        action_object_equivalent_embeddings = NLPUtil.SBERT_MODEL.encode(action_object_equivalent_names)
        pairs_list = sentence_transformers.util.semantic_search(action_embeddings,
                                                                action_object_equivalent_embeddings,
                                                                top_k=len(action_object_equivalent_embeddings))
        # pairs_list = NLPUtil.get_pairs_with_cossim_by_decreasing(action_embeddings, action_object_equivalent_embeddings)
        for pairs_index, pairs in tqdm(enumerate(pairs_list), ascii=True):
            step = step_list[pairs_index]
            if step.concepts_in_target and step.action:
                # if len(step.concepts_in_target) == 1:
                step_target_categories = set()
                for concept in step.concepts_in_target:
                    step_target_categories.add(concept.category.name)
                for pair in pairs:
                    if pair['score'] >= ACTION_MERGE_THRESHOLD:
                        action_object = index_action_object_dict[pair['corpus_id']]
                        if action_object.category.name in step_target_categories:
                            step.action_object = action_object
                            break

    def extract_categories(self):
        """
        extract categories from bugs
        construct static part (all categories and all concepts)
        @return: category_concept_dict
        @rtype: dict
        """
        concept_category_dict = dict()
        for bug in tqdm(self.bugs):
            # print(bug.id)
            if bug.description.steps_to_reproduce:
                for step in bug.description.steps_to_reproduce:
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

        # print(len(concept_category_dict.keys()))
        # print(concept_category_dict.keys())
        # print(concept_category_dict)

        # get category_concept_dict
        category_concept_dict = Category.get_category_concept_dict(concept_category_dict)
        # convert concept_set into concept_list
        for category, concepts in category_concept_dict.items():
            category_concept_dict[category] = list(concepts)

        # # construct category object and concept object
        # categories, concepts = Category.get_static_part(category_concept_dict)
        # return categories, concepts
        return category_concept_dict

    def matching(self, need_to_match_step):
        """
        match the need to match step with steps in bugs
        @param need_to_match_step:
        @type need_to_match_step:
        @return: bug_possible_steps: key: bug, value: possible_steps in bug
        @rtype: dict
        """
        words = NLPUtil.preprocess(need_to_match_step.text)
        # print(words)
        bug_possible_steps = dict()

        related_concepts = list()

        for index, bug in tqdm(enumerate(self.bugs)):
            if bug.description.steps_to_reproduce:
                for step in bug.description.steps_to_reproduce:
                    if step.concepts:
                        for concept in step.concepts:
                            concept_words = NLPUtil.preprocess(concept.name)
                            # print(concept_words)
                            if list(set(words) & set(concept_words)):
                                # if not flag or flag != index:
                                bug_possible_steps[bug] = bug_possible_steps.get(bug, list())
                                bug_possible_steps[bug].append(step)
                                # if step contains other concept
                                related_concepts.extend(step.concepts)
        # for bug in bug_possible_steps.keys():
        #     extend_possible_steps = []
        #     for step in bug.description.steps_to_reproduce:
        #         if list(set(step.concepts) & set(related_concepts)):
        #             extend_possible_steps.append(step)
        #     if extend_possible_steps:
        #         bug_possible_steps[bug] = extend_possible_steps

        return bug_possible_steps

    @staticmethod
    def complete_steps(bug_possible_steps):
        """
        complete steps in bug possible steps:
        if steps in bug is A->B->C->D->E
           possible steps in bug is A, C, E
        then complete it into A, B, C, D, E
        @return: completed bug_possible_steps
        @rtype: dict
        """
        for bug in bug_possible_steps.keys():
            possible_steps = list()
            steps = bug_possible_steps[bug]
            # print(steps)
            num = len(steps)
            # print(num)
            step = steps[0]
            # print(step.next_step)
            # print(type(step.next_step))
            # print(step)
            # print(steps[num - 1])
            if num > 1:
                possible_steps.append(step)
                while step.next_step != steps[num - 1]:
                    step = step.next_step
                    possible_steps.append(step)
                possible_steps.append(steps[num - 1])
                bug_possible_steps[bug] = possible_steps

            # only link one step, then contains steps from the start to this one
            elif num == 1 and len(bug.description.steps_to_reproduce) > 1:
                # possible_steps = list()
                step_start = bug.description.steps_to_reproduce[0]
                # possible_steps.append(step_start)
                while step_start != step:
                    possible_steps.append(step_start)
                    step_start = step_start.next_step
                possible_steps.append(step)
                bug_possible_steps[bug] = possible_steps

            # bug_possible_steps[bug] = possible_steps
        return bug_possible_steps

    def get_steps(self):
        """
        get bugs' step list and step text list
        @return: step_list, step_text_list
        @rtype: object_list, string_list
        """
        step_list = list()
        step_text_list = list()
        for bug in self.bugs:
            if bug.description.steps_to_reproduce:
                for step in bug.description.steps_to_reproduce:
                    step_list.append(step)
                    step_text_list.append(step.text)

        return step_list, step_text_list

    def merge_steps_by_paraphrase_mining(self, model):
        """
        When there are huge number of sentences (steps), it gets poor performance
        due to [{1, 2}, {2, 3}, {4, 5}, {6, 2}, {7, 5}, {8, 9}] -> [{1, 2, 3, 6}, {4, 5, 7}, {8, 9}]
        score(1, 2) >= Threshold, score(2, 3) >= Threshold, but how about score(1,3) ? Threshold
        This transfer will result in low similarities in a cluster when dataset is huge.
        merge steps:
        1. get step cos_sim matrix
        2. get index_pairs with score >= THRESHOLD
        3. merge index_pairs into index_clusters, e.g. [{1, 2}, {2, 3}, {4, 5}, {6, 2}, {7, 5}, {8, 9}]
                                                        -> [{1, 2, 3, 6}, {4, 5, 7}, {8, 9}]
        4. Merge steps by index_clusters (if (not concepts_in_target) or (not action_object))
        5. Merge steps by concepts (if concepts_in_target and action_object)
        6. Merge the rest steps (each is a cluster)
        7. Get self.step_index_cluster_dict and assign index for Step.cluster_index

        @param model: SBERT
        @type model: sentence embedding
        @return: self.step_index_cluster_dict, Step.cluster_index
        @rtype: dict{ key: index, value: cluster ((set(step(object), step(object), ...))}), int (index)
        """
        step_list, step_text_list = self.get_steps()

        clusters = list()
        logging.warning("Get step cos_sim matrix...")
        # (score, i, j) list
        paraphrases = util.paraphrase_mining(model, step_text_list, show_progress_bar=True)
        logging.warning("merge index_pairs into index_clusters by paraphrases...")
        index_clusters = list()
        for paraphrase in tqdm(paraphrases):
            score, p_i, p_j = paraphrase
            if score >= STEP_MERGE_THRESHOLD:
                index_clusters.append({p_i, p_j})

        logging.warning("merge sets with intersection in list...")
        index_clusters = ListUtil.merge_sets_with_intersection_in_list(index_clusters)

        # merging_steps = list()
        steps_num = len(step_list)
        step_index_set = set()

        logging.warning("Merging steps by cos...")
        for index_cluster in tqdm(index_clusters, ascii=True):
            cluster = set()
            for index in index_cluster:
                if (not step_list[index].concepts_in_target) or (not step_list[index].action_object):
                    cluster.add(step_list[index])
                    step_index_set.add(index)
            if cluster:
                clusters.append(cluster)

        logging.warning("Merging steps by concepts...")
        for i, step_i in tqdm(enumerate(step_list)):

            if i not in step_index_set and step_i:

                # merging_step_i_list = list()
                # merging_step_i_list.append(step_i)
                concepts_in_target_i = step_i.concepts_in_target
                action_object_i = step_i.action_object
                if concepts_in_target_i and action_object_i:
                    cluster_i = set()
                    cluster_i.add(step_i)
                    step_index_set.add(i)
                    j = i + 1
                    while j < steps_num:
                        if j not in step_index_set and step_list[j] and step_list[j].concepts_in_target and step_list[
                            j].action_object:
                            if concepts_in_target_i == step_list[j].concepts_in_target and action_object_i == step_list[
                                j].action_object:
                                cluster_i.add(step_list[j])
                                step_index_set.add(j)
                                # step_i.merge_steps.add(step_list[j])
                                # step_list[j].merge_steps.add(step_i)
                        j = j + 1
                    # else:
                    if cluster_i:
                        clusters.append(cluster_i)
        logging.warning("Merging the rest steps...")
        for index, step in enumerate(step_list):
            if index not in step_index_set:
                cluster = set()
                cluster.add(step)
                clusters.append(cluster)
        index_cluster_dict = dict()
        for index, cluster in enumerate(clusters):
            index_cluster_dict[index] = index_cluster_dict.get(index, cluster)
            for step in cluster:
                step.cluster_index = index

        self.step_index_cluster_dict = index_cluster_dict

    def merge_steps_by_fast_clustering(self, model):
        """
        https://www.sbert.net/examples/applications/clustering/README.html
        Fast Clustering

        merge steps:
        1. Merge steps by concepts (if concepts_in_target and action_object)
        2. Merge steps by fast clustering
        3. Get self.step_index_cluster_dict and assign index for Step.cluster_index

        @param model: SBERT
        @type model: sentence embedding
        @return: self.step_index_cluster_dict, Step.cluster_index
        @rtype: dict{ key: index, value: cluster ((set(step(object), step(object), ...))}), int (index)
        """
        clusters = list()
        step_list, step_text_list = self.get_steps()
        logging.warning("Cluster steps by Concept in Target and Action...")
        steps_num = len(step_text_list)
        # print(steps_num)
        step_index_set = set()
        for i, step_i in tqdm(enumerate(step_list), ascii=True):
            if i not in step_index_set and step_i:
                concepts_in_target_i = step_i.concepts_in_target
                action_object_i = step_i.action_object
                if concepts_in_target_i and action_object_i:
                    cluster_i = set()
                    cluster_i.add(step_i)
                    step_index_set.add(i)
                    j = i + 1
                    while j < steps_num:
                        if j not in step_index_set and step_list[j] and step_list[j].concepts_in_target and step_list[
                            j].action_object:
                            if concepts_in_target_i == step_list[j].concepts_in_target and action_object_i == step_list[
                                j].action_object:
                                cluster_i.add(step_list[j])
                                step_index_set.add(j)
                        j = j + 1
                    # else:
                    if cluster_i:
                        clusters.append(cluster_i)
        # remove steps in step_index_set
        for index in sorted(step_index_set, reverse=True):
            del step_text_list[index]
            del step_list[index]
        # step_num_concept = 0
        # for cluster in clusters:
        #     step_num_concept = step_num_concept + len(cluster)
        # print(step_num_concept)
        logging.warning("Cluster steps by Fast Clustering...")
        step_index_set = set()
        # (score, i, j) list
        step_embeddings = model.encode(step_text_list, batch_size=SBERT_BATCH_SIZE, show_progress_bar=True,
                                       convert_to_tensor=True)
        # step_embeddings = FileUtil.load_pickle(Path(DATA_DIR, 'step_embeddings.json'))
        # FileUtil.dump_pickle(Path(DATA_DIR, 'step_embeddings.json'), step_embeddings)
        step_embeddings = step_embeddings.to('cpu')

        # print(len(step_embeddings))

        # Two parameters to tune:
        # min_cluster_size: Only consider cluster that have at least 25 elements
        # threshold: Consider sentence pairs with a cosine-similarity larger than threshold as similar
        # Returns only communities that are larger than min_community_size.
        init_max_size = 1000
        if len(step_embeddings) < 1000:
            init_max_size = len(step_embeddings)
        index_clusters = util.community_detection(step_embeddings, threshold=STEP_MERGE_THRESHOLD, min_community_size=1,
                                                  init_max_size=init_max_size)
        # step_num = 0
        # for index_cluster in index_clusters:
        #     step_num = step_num + len(index_cluster)
        # print(step_num)

        for index_cluster in index_clusters:
            cluster = set()
            for index in index_cluster:
                cluster.add(step_list[index])
                step_index_set.add(index)
            clusters.append(cluster)

        logging.warning("Merging the rest steps...")
        for index, step in enumerate(step_list):
            if index not in step_index_set:
                cluster = set()
                cluster.add(step)
                clusters.append(cluster)

        index_cluster_dict = dict()
        for index, cluster in enumerate(clusters):
            index_cluster_dict[index] = index_cluster_dict.get(index, cluster)
            for step in cluster:
                step.cluster_index = index

        self.step_index_cluster_dict = index_cluster_dict

        # steps_num_in_cluster = 0
        #
        # for index, cluster in self.step_index_cluster_dict.items():
        #     print(index)
        #     print(cluster)
        #     steps_num_in_cluster = steps_num_in_cluster + len(cluster)
        #     print("###################################################")

        # for cluster in clusters:
        #     print(cluster)
        #     steps_num_in_cluster = steps_num_in_cluster + len(cluster)
        #     print("###################################################")

        # print(steps_num)
        # print(steps_num_in_cluster)

    # def extract_actions(self, category_concept_dict):
    #     """
    #     extract actions from bugs
    #     @param category_concept_dict: key: category, value: concepts (set)
    #     @type category_concept_dict:
    #     @return:
    #     @rtype:
    #     """
    #     category_action_dict = dict()
    #     # action_count_dict = dict()
    #     for bug in tqdm(self.bugs):
    #         if bug.description.steps_to_reproduce:
    #             for step in bug.description.steps_to_reproduce:
    #                 print("*************************************************")
    #                 print(step)
    #                 step = SeedExtractor.replace_seed_by_placeholder(step)
    #                 print(step)
    #                 if len(step) > 1024:
    #                     print("******************too long*******************************")
    #                     continue
    #                 category_action_dict = Action.categorize_actions_by_concept(step, category_concept_dict,
    #                                                                             category_action_dict)
    #     return category_action_dict

    # def match_concepts_for_steps(self, categories):
    #     concepts = Concepts(categories.get_concepts())
    #     target_list = []
    #     concept_list = []
    #     for bug in self.bugs:
    #         for step in bug.description.steps_to_reproduce:
    #             target_list.append(step.target)
    #
    #     concept_in_target = None
    #     if target_list:
    #         pairs_list = NLPUtil.get_pairs_with_cossim_by_decreasing([target], concepts.concept_name_list)
    #         top_1_pairs = NLPUtil.get_top_1_pairs_with_cossim(pairs_list)
    #         concept_index = top_1_pairs[0]['index'][1]
    #         if top_1_pairs[0]['score'] >= THRESHOLD:
    #             concept_in_target = concepts.find_concept_by_name(concepts.concept_name_list[concept_index])
