from pathlib import Path

from bs4 import BeautifulSoup
from tqdm import tqdm

from bug_improving.types.element import Element
from bug_improving.utils.file_util import FileUtil
from config import OUTPUT_DIR, DATA_DIR

if __name__ == "__main__":
    # component = "about_logins"
    # ftl_filename = "aboutLogins_ftl.json"
    # html_filename = "aboutLogins.html"
    component = "about_preferences"
    ftl_filename = "preferences_ftl.json"
    html_filename = "preferences_from_scrape_url.xhtml"
    filepath = Path(OUTPUT_DIR, "firefox_gui", component, ftl_filename)

    ftl_dict = FileUtil.load_json(filepath)

    elements = []

    if "body" in ftl_dict.keys():
        element_dict_list = ftl_dict["body"]
        for element_dict in element_dict_list:
            element = Element.from_dict(element_dict)
            if element:
                elements.append(element)
    name_count = 0
    for element in elements:
        if element.name:
            name_count = name_count + 1
    #     else:
    #         print(element)
    #     # print(element)
    #
    # print(len(elements))
    # print(name_count)
    print("******************************************************************")

    # print(about_logins_ftl)
    # extract category from html
    filepath = Path(DATA_DIR, "firefox_gui", component, html_filename)
    with open(filepath, 'r') as result_page:
        soup = BeautifulSoup(result_page, 'html.parser')
    count = 0
    tags = dict()
    for element in tqdm(elements):
        # tags = soup.findAll(attrs={"data-l10n-id": element.id})
        tag = soup.find(attrs={"data-l10n-id": element.id})
        element.get_category_from_html(tag)
        print("*************************************************")
        # print(element)
        # print(tag)
        if tag:

            tags[tag.name] = tags.get(tag.name, 0) + 1
            # element.category = tag.name
            count = count + 1
            print(element)
            print(tag.name)
            # print(type(tag.name))
            print(tag.parent.name)
            # print(type(tag.parent.name))
            print(tag.parent.parent.name)
            # print(type(tag.parent.parent.name))
            print(tag.attrs)
            # print(type(tag.attrs))
            # print(tag.parent.parent.name)
    print(count)
        # else:
        #     print(element)
        # print(element)
        # print(tag.name)

        # input()
    print("******************************************************************")
    # for key in tags.keys():
    #     print(f"{key}: {tags[key]}")
    category_element_dict = dict()
    for element in elements:
        category_element_dict[element.category] = category_element_dict.get(element.category, [])
        category_element_dict[element.category].append(element)
        # print(element)
    for key, elements in category_element_dict.items():
        print("#############################")
        print(key)
        for element in elements:
            print(element)
