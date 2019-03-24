# encoding = utf-8

import sys
import requests
import argparse
import unicodecsv as csv
from StringIO import StringIO
from functools import partial
from multiprocessing import Pool

import django
django.setup()
from sefaria.system.exceptions import InputError
# from sefaria.export import import_versions_from_stream
from sefaria.tracker import modify_text
from sefaria.model import *


def version_urls(server, book_title):
    version_list_url = u'{}/api/texts/versions/{}'.format(server, book_title)
    version_list = requests.get(version_list_url).json()
    for v in version_list:
        yield u'{}/download/version/{} - {} - {}.json'.format(server, book_title, v[u'language'], v[u'versionTitle'])


def pull_text_from_server(url, uid):
    response = requests.get(url)
    # import_versions_from_stream(StringIO(response.text.encode('utf-8')), [1], uid)
    # my_stream = StringIO(response.text.encode('utf-8'))
    # csv.field_size_limit(sys.maxsize)
    # reader = csv.reader(my_stream)
    # rows = [row for row in reader]
    make_version(response.json(), uid)


def derive_ref(node_list):
    if node_list[-1] == u'':
        node_list = node_list[:-1]
    ref_string = u', '.join(node_list)
    return Ref(ref_string).default_child_ref()


def get_text(text_json, node_list):
    if isinstance(text_json, dict):
        child_nodes = node_list[1:]
        return get_text(text_json[child_nodes[0]], child_nodes)
    else:
        return text_json


def move_through_schema(version_schema, callback_method):
    """
    add node
    if nodes:
        recurse through children
    else:
        run callback
    pop node
    """
    def move(node_schema, callback, node_list):

        node_list.append(node_schema["enTitle"])

        if "nodes" in node_schema:
            for node in node_schema["nodes"]:
                move(node, callback, node_list)
        else:
            callback(node_list)
        node_list.pop()

    root_node = version_schema.get('schema', None)
    if root_node:
        move(root_node, callback_method, [])
    else:
        callback_method([version_schema["title"]])


def save_text(user_id, version_title, version_lang, action_type, text_json):
    def modify_ja(node_list):
        my_ref = derive_ref(node_list)
        my_text = get_text(text_json['text'], node_list)
        modify_text(user_id, my_ref, version_title, version_lang, my_text, type=action_type)

    move_through_schema(text_json, modify_ja)


def save_row(user_id, version_title, version_lang, action_type, row):
    ref = Ref(row[0])
    print "Saving: {}".format(ref.normal())
    try:
        modify_text(user_id, ref, version_title, version_lang, row[1], type=action_type)
    except InputError:
        pass


def make_version(text_json, user_id):
    index_title = text_json['title']
    index_node = Ref(index_title).index_node

    action = "edit"
    version_title = text_json['versionTitle']
    version_lang = text_json['language']

    v = Version().load({
        "title": index_title,
        "versionTitle": version_title,
        "language": version_lang
    })

    if v is None:
        action = "add"
        v = Version({
            "chapter": index_node.create_skeleton(),
            "title": index_title,
            "versionTitle": version_title,
            "language": version_lang,  # Language
            "versionSource": text_json['versionSource'],  # Version Source
            "versionNotes": text_json.get('versionNotes', ''),  # Version Notes
        }).save()

    # partial_row_save = partial(save_row, user_id, version_title, version_lang, action)
    # pool = Pool()
    # text_rows = rows[5:]
    # pool.map(partial_row_save, text_rows)
    save_text(user_id, version_title, version_lang, action, text_json)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("title", help="title argument")
    parser.add_argument("server", help="server from which to pull")
    parser.add_argument("uid", help="user id number")

    args = parser.parse_args()
    for u in version_urls(args.server, args.title):
        pull_text_from_server(u, args.uid)
