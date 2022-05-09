import requests
import json
import base64


def get_attachment_by_id(id):
    url = 'https://bugzilla.mozilla.org/rest/bug'
    bug_id = "/{}".format(id)
    bug_attachment = "/attachment"
    bug_attachment_url = url + bug_id + bug_attachment

    try:
        search_results_attachment = requests.get(bug_attachment_url)
        response_data_attachment = json.loads(search_results_attachment.text)
        bugs_attachment = response_data_attachment["bugs"]
    except KeyError as e:
        bugs_attachment = {str(id): []}
    # video, picture, radio (mp3)
    file_type_list = ["bmp", "jpg", "png", "tif", "gif", "pcx", "tga", "exif", "fpx", "svg", "psd", "cdr", "pcd", "dxf",
                      "ufo", "eps", "ai", "raw", "WMF", "webp", "avif", "apng", "avi", "wmv", "mpeg", "mp4", "m4v",
                      "mov", "asf", "flv", "f4v", "rmvb", "rm", "3gp", "vob", "mp3"]

    bug_attachment_details = bugs_attachment[str(id)]
    file_list = []

    if len(bug_attachment_details) > 0:
        for h in range(len(bug_attachment_details)):
            attachment_id = bug_attachment_details[h]["id"]
            attachment_data = bug_attachment_details[h]["data"]
            attachment_file_name = bug_attachment_details[h]["file_name"]
            file_type = attachment_file_name.split(".")[-1]
            if file_type in file_type_list:
                if attachment_data is not None:
                    # write attachment into file
                    decodeit = open("./attachment_tmp_files/{}_{}_{}".format(id, attachment_id, attachment_file_name),
                                    'wb')
                    decodeit.write(base64.b64decode(attachment_data))
                    decodeit.close()
                    # write attachment into file
                    file_dic = {"id": id, "attachment_id": attachment_id, attachment_file_name: "attachment_file_name",
                                "attachment_data": base64.b64decode(attachment_data)}
                    file_list.append(file_dic)
    return file_list


if __name__ == '__main__':
    # for i in range(100):
    attachment_data = get_attachment_by_id(1629538)
    print(len(attachment_data))
