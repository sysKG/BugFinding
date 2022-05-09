"""
get bugs of github from file
covert bugs into bugs object
"""
from bug_improving.types.for_github.bug import Bug, Bugs
from bug_improving.utils.file_util import FileUtil
from bug_improving.utils.path_util import PathUtil

if __name__ == "__main__":

    issues = FileUtil.load_json(PathUtil.get_bugs_filepath("k9mail_k-9"))
    bugs = list()
    for issue in issues:
        bug = Bug.from_dict(issue)
        # print(bug)
        # if bug.id == "https://api.github.com/repos/k9mail/k-9/issues/4016":
        #     print(bug)
        bugs.append(bug)

    bugs = Bugs(bugs)
    print(bugs.get_length())

    bugs = bugs.get_specified_label_bugs("bug")
    print(bugs.get_length())
    bugs_with_stp = list()
    for bug in bugs:
        if bug.description.steps_to_reproduce:
            bugs_with_stp.append(bug)
    print(len(bugs_with_stp))
    for bug in bugs_with_stp:
        print(bug.id)
        print(bug.summary)
        print(bug.description.steps_to_reproduce)
        print(bug.description.expected_results)
        print(bug.description.actual_results)
