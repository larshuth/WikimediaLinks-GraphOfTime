import node_edge_timeline_creation
import time
import os
import pickle


def remapping_dicts_multiple_wikis():
    global_map = dict()
    value_map = dict()
    for file in os.listdir():
        if 'map_' in file and '.pkl' in file:
            local_map = pickle.load(file)
            if file[-8:-4] == 'wiki':
                wiki = file[4:-8]
            else:
                wiki = file[4:-4]
            if global_map == dict():
                global_max_value = 0
            else:
                global_max_value = global_map[max(global_map, key=global_map.get)]
            value_map[wiki] = global_max_value
            for local_key in local_map:
                global_key = wiki + ':' + local_key
                global_map[global_key] = local_map[local_key] + global_max_value
    return global_map


def no_remapping_only_new_values(unsorted_log, map, current_max_value):
    with open('textlog_edges-' + wiki + '.json', 'r') as log:
        for line in log:
            new_line = line[:20]
            for i in range(20, len(line)):
                link_open_one = False
                link_open_two = False
                link_string = ''
                if line[i] == '[':
                    while line[i] != ']':
                        if line[i] == "'" and not (link_open_one or link_open_two):
                            link_open_one = True
                        elif line[i] == '"' and not (link_open_one or link_open_two):
                            link_open_two = True
                        elif line[i] != "'" and link_open_one:
                            link_string += line[i]
                        elif line[i] != '"' and link_open_two:
                            link_string += line[i]
                        elif line[i] == "'" and link_open_one:
                            try:
                                new_line += str(map[link_string])
                            except KeyError:
                                # print('here')
                                map[link_string] = current_max_value + 1
                                current_max_value += 1
                                new_line += str(current_max_value)
                            link_string = ''
                            link_open_one = False
                        elif line[i] == '"' and link_open_two:
                            try:
                                new_line += str(map[link_string])
                            except KeyError:
                                # print('here')
                                map[link_string] = current_max_value + 1
                                current_max_value += 1
                                new_line += str(current_max_value)
                            link_string = ''
                            link_open_two = False
                        else:
                            new_line += line[i]
                        i += 1
                    new_line += ']},\n'
                else:
                    new_line += line[i]
            unsorted_log.write(new_line)
    return map


def remapping_everything(unsorted_log, map, current_max_value):
    with open('textlog_edges-' + wiki + '.json', 'r') as log:
        for line in log:
            new_line = line[:20]
            for i in range(20, len(line)):
                link_open_one = False
                link_open_two = False
                link_string = ''
                if line[i] == '[':
                    while line[i] != ']':
                        if line[i] == "'" and not (link_open_one or link_open_two):
                            link_open_one = True
                        elif line[i] == '"' and not (link_open_one or link_open_two):
                            link_open_two = True
                        elif line[i] != "'" and link_open_one:
                            link_string += line[i]
                        elif line[i] != '"' and link_open_two:
                            link_string += line[i]
                        elif line[i] == "'" and link_open_one:
                            try:
                                new_line += str(map[link_string])
                            except KeyError:
                                # print('here')
                                map[link_string] = current_max_value + 1
                                current_max_value += 1
                                new_line += str(current_max_value)
                            link_string = ''
                            link_open_one = False
                        elif line[i] == '"' and link_open_two:
                            try:
                                new_line += str(map[link_string])
                            except KeyError:
                                # print('here')
                                map[link_string] = current_max_value + 1
                                current_max_value += 1
                                new_line += str(current_max_value)
                            link_string = ''
                            link_open_two = False
                        else:
                            new_line += line[i]
                        i += 1
                    new_line += ']},\n'
                else:
                    new_line += line[i]
            unsorted_log.write(new_line)
    return map


def remapping_string_links(map, wiki, value_map=dict()):
    if value_map == dict():
        value_map[wiki] = 0
    current_max_value = map[max(map, key=map.get)]      # determining current max value in the dict mapping page_title
                                                        # to page_id to
    unsorted_log = open('unsorted_log-' + wiki + '.json', 'w')
    if len(value_map) == 1:
        map = no_remapping_only_new_values(unsorted_log, map, current_max_value)
    elif len(value_map) > 1:
        map = remapping_everything(unsorted_log, map, current_max_value)
    return map

