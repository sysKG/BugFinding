import csv
import queue

import spacy
from tqdm import tqdm

from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":
    bugs = FileUtil.load_pickle(PathUtil.get_filtered_bugs_filepath())
    print('#datapoints: {}\n'.format(bugs.get_length()))

    print('Loading spaCy model...\n')
    nlp = spacy.load('en_core_web_sm')
    print('Loaded.\n')

    # Parse sentences
    keyphrases = ['after', 'before', 'as soon as', 'when', 'while', 'whenever', 'every time', 'until', 'then']
    kept_verb_deps = ['ROOT', 'advcl', 'conj']
    parsed_sents = []

    print('Processing...\n')
    for bug in tqdm(bugs):
        summary = bug.summary
        # print(summary)
        summary = summary.replace('as soon as', 'when')
        summary = summary.replace('As soon as', 'When')
        summary = summary.replace('every time', 'whenever')
        summary = summary.replace('Every time', 'Whenever')

        kept_sent_ids = []

        sents = list(nlp(summary, disable=['ner']).sents)

        for sid, sent in enumerate(sents):
            has_verb = False
            has_advcl = False  # a sentence either has advcl or 'then'
            has_key = False
            has_then = False
            for token in sent:
                if token.tag_.startswith('V') and token.dep_ in kept_verb_deps:
                    has_verb = True
                    if token.dep_ == 'advcl':
                        has_advcl = True
                if token.text.lower() in keyphrases[:-1]:
                    has_key = True
                if token.text.lower() == 'then':
                    has_then = True
                if (has_advcl and has_key) or (has_verb and has_then):
                    break
            if (has_advcl and has_key) or (has_verb and has_then):
                # also consider surrounding sentences
                kept_sent_ids.append(sid - 1)
                kept_sent_ids.append(sid)
                kept_sent_ids.append(sid + 1)

        one_story = []
        for sid in range(len(sents)):
            if sid in kept_sent_ids:
                # SID is ID for review
                # sid is ID for sentence
                one_story.append((f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug.id}", sid, sents[sid]))
        if len(one_story) > 0:
            parsed_sents.append(one_story)

    print('Done. # Kept Stories: {}\n'.format(len(parsed_sents)))

    # Extract events
    event_sequences = []
    print('Getting event sequences...\n')

    for one_story in tqdm(parsed_sents):
        # if (idx + 1) % 10000 == 0:
        #     print('Processing... {} / {}\n'.format((idx + 1), len(parsed_sents)))

        events = []

        for SID, sid, sent in one_story:
            verbs = []
            for token in sent:
                if token.dep_ in kept_verb_deps:
                    verbs.append(token)

            local_events = []
            key_sentence = False
            # dict: verb to key word
            verb_key = {}
            # for each verb, get its children
            for verb in verbs:

                if verb.dep_ == 'conj' and verb.head in verb_key:
                    verb_key[verb] = verb_key[verb.head]
                else:
                    verb_key[verb] = 'non'

                verb_flags = [verb]
                verb_queue = queue.Queue()
                verb_queue.put(verb)

                while not verb_queue.empty():
                    cur = verb_queue.get()
                    for t in sent:
                        if t.head == cur and (not t in verbs):
                            if t.dep_ == 'cc' and t.head == verb:
                                continue
                            if t.text.lower() in keyphrases and t.head == verb:
                                verb_key[verb] = t.text.lower()
                                key_sentence = True
                                continue
                            verb_queue.put(t)
                            verb_flags.append(t)
                # remove punctuations and conjunction words
                started = False
                is_question = False
                verb_children = []
                for t in reversed(sent):
                    if not t in verb_flags:
                        continue
                    if t.tag_ == '_SP':
                        continue
                    if t.text == '?':
                        is_question = True
                        break
                    if not started:
                        if t.dep_ == 'punct':
                            pass
                        elif t.dep_ == 'cc':
                            pass
                        elif t.tag_ == '.':
                            pass
                        else:
                            started = True
                    if started:
                        verb_children.append(t)

                if is_question:
                    continue
                if len(verb_children) <= 1:
                    continue
                verb_children.reverse()

                # another way to check punctuations
                if verb_children[0].dep_ == 'punct':
                    verb_children = verb_children[1:]
                if len(verb_children) <= 1:
                    continue

                local_events.append((verb, verb_children, sent))
            if key_sentence:
                for verb in verb_key:
                    if verb_key[verb] == 'non':
                        verb_key[verb] = 'out'
            for verb, verb_children, sent in local_events:
                # keep lemma
                events.append((SID, sid, verb, verb_key[verb], verb_children, sent))
        if len(events) > 1:
            event_sequences.append(events)
    print('Done. #Stories: {}'.format(len(event_sequences)))

    print('Writing to file...\n')

    with open(PathUtil.get_events_filepath(), 'w') as file:
        writer = csv.writer(file)
        writer.writerow(("URL", "sentenceID", "verb", "verb_lemma", "verb_type", "event_phrase"))

        for events in event_sequences:
            for SID, sid, verb, vk, verb_children, sent in events:
                tp = (SID, sid, verb.text, verb.lemma_, vk, ' '.join([t.text for t in verb_children]))
                writer.writerow(tp)

    print('Written to file.\n')

