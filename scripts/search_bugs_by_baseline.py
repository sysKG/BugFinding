from pathlib import Path

from sentence_transformers import SentenceTransformer, util
# import torch
import json
from tqdm import tqdm
import timeit

from config import DATA_DIR


def read_json_files(path, encoding):
    f = open(path, encoding=encoding)
    json_file = json.load(f)
    f.close()
    return json_file


def generate_text_list(bug_list, only_summary):
    bug_text_list = []
    for bug in bug_list:
        bug_summary = bug["summary"]
        bug_description = bug["comments"][0]["text"]
        if only_summary:
            bug_text = bug_summary
        else:
            bug_text = bug_summary + ".\n" + bug_description
            # print(bug_text)
        bug_text_list.append(bug_text)
    return bug_text_list


def get_query_bug_text(bug_list, bug_id, only_summary):
    for bug in bug_list:
        b_id = bug["id"]
        if b_id == bug_id:
            bug_summary = bug["summary"]
            bug_description = bug["comments"][0]["text"]
            if only_summary:
                bug_text = bug_summary
            else:
                bug_text = bug_summary + ".\n" + bug_description
                # print(bug_text)
            return bug_text
    return None


def search_top_k_bugs(use_cuda, model, top_k, bug_id, bug_path):
    if use_cuda:
        device = "cuda"
    else:
        device = "cpu"

    bugs = read_json_files(bug_path, encoding='utf-8')
    corpus = generate_text_list(bugs, only_summary=False)
    embedder = SentenceTransformer(model)
    query = [get_query_bug_text(bugs, bug_id, False)]

    corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True).to(device)
    query_embedding = embedder.encode(query, convert_to_tensor=True).to(device)
    hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=top_k)

    searched_bug_list = []
    for hit in hits[0]:
        hit_id = hit["corpus_id"]
        bug = bugs[hit_id]
        searched_bug_list.append((hit["score"], bug))
    return searched_bug_list


if __name__ == '__main__':
    use_cuda = True
    # model = 'all-MiniLM-L6-v2'
    top_k = 20
    bug_id = 1678633
    bugs_path = Path(DATA_DIR, "filtered_bugs_for_baseline.json")

    bug_list = search_top_k_bugs(use_cuda=use_cuda, model='paraphrase-MiniLM-L6-v2',
                                 top_k=top_k, bug_id=bug_id, bug_path=bugs_path)
    for score, bug in bug_list:
        print(f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug['id']} : {score}")
        print(bug['summary'])
        print(bug["comments"][0]["text"])
        print("###################################################################")
    # print(bug_list)
