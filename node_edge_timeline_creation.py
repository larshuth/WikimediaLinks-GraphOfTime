import re
import time
import os
import pickle

t0 = time.time()


def create_title_id_mapping(wiki, namespaces=set()):
    '''Parse through file and get the internal page id for every available page title. short_file is the path to the
    file contatining only <title> and <id> lines'''
    list_of_wikis = ['wikipedia', 'wiktionary', 'wikinews', 'wikibooks', 'wikiquote', 'wikisource', 'oldwikisource',
                     'wikispecies', 'wikiversity', 'wikivoyage', 'wikimedia', 'foundation', 'commons', 'wikidata']
    shortened = {'wikipedia': 'w', 'w': 'w', 'wiktionary': 'wikt', 'wikt': 'wikt', 'wikinews': 'n', 'n': 'n',
                 'wikibooks': 'b', 'b': 'b', 'wikiquote': 'q', 'q': 'q', 'wikisource': 's', 's': 's',
                 'oldwikisource': 'oldwikisource', 'wikispecies': 'species', 'species': 'species', 'wikiversity': 'v',
                 'v': 'v', 'wikivoyage': 'voy', 'voy': 'voy', 'wikimedia': 'wmf', 'foundation': 'wmf', 'wmf': 'wmf',
                 'commons': 'c', 'c': 'c', 'wikidata': 'd', 'd': 'd'}
    title_id_map = dict()
    if wiki[-4:] == 'wiki':
        wiki_internal = 'w:' + wiki[:-4] + ':'
    else:
        for interwiki in list_of_wikis:
            if wiki[-len(interwiki):].lower() == interwiki:
                wiki_internal = shortened[interwiki] + ':' + wiki[:-len(interwiki)] + ':'
                found = True
                break
        if not found:
            print('ERROR project not found')
    for short_file in os.listdir(wiki + '/'):
        if 'pagetitleidmap' in short_file:
            with open(wiki + '/' + short_file) as f:
                for line in f:
                    if line[5] == 't':
                        key = wiki_internal + line[11:-9]
                    elif line[5] == 'i':
                        title_id_map[key] = int(line[8:-6])
                    else:
                        pos = 40
                        namespace = ''
                        space = True
                        while line[pos] != '>':
                            if line[pos] == ' ':
                                space = False
                                break
                            pos += 1
                        if space:
                            pos += 1
                            while line[pos] != '<':
                                try:
                                    namespace += line[pos]
                                except IndexError:
                                    print(line)
                                pos += 1
                            namespace = namespace + ':'
                            namespaces |= {namespace}
    print(title_id_map)
    return title_id_map, namespaces


def save_map(title_id_map, wiki):
    '''Saving a dictionary using pickle.'''
    with open('title_id_map_' + wiki +'.pkl', 'wb') as file:
        pickle.dump(title_id_map, file)
    return


def load_map(wiki):
    '''Loading a dictionary that was saved using pickle.'''
    with open('title_id_map_' + wiki +'.pkl', 'rb') as file:
        title_id_map = pickle.load(file)
    return title_id_map


def remapping_dicts_multiple_wikis(dicts):
    '''Combining all the different saved title_id_maps into one big to be used in the creation of the edge and node
    textlogs later on.'''
    print('Combining dicts of different language wikis.')
    global_map = dict()
    value_map = dict()      # map to indicate in which range of id's the pages of a specific wiki fall
    directories = os.listdir()
    for file_name in directories:
        if 'title_id_map_' in file_name and '.pkl' in file_name and file_name[13:-4] in dicts:
            with open(file_name, 'rb') as file:
                local_map = pickle.load(file)
            wiki = file_name[13:-4]
            if global_map == dict():
                global_max_value = 0
            else:
                global_max_value = global_map[max(global_map, key=global_map.get)]
            value_map[wiki] = global_max_value
            for local_key in local_map:
                global_map[local_key] = local_map[local_key] + global_max_value
    save_map(global_map, 'global_only_existing_nodes')
    with open('value_map.pkl', 'wb') as file:
        pickle.dump(value_map, file)
    return global_map, value_map

def get_namespaces_inefficient(languages):
    namespaces = set()
    for wiki in languages:
        for file in os.listdir(wiki + '/'):
            os.system("7za e -so " + wiki + '/' + file + r" | sed -n '/^ \{6\}<namespace/p' -> " + wiki
            + "/namespaces-" + wiki + ".txt")
            with open(wiki + "/namespaces-" + wiki + ".txt") as namespace_text:
                for line in namespace_text:
                    try:
                        if line[6:16] == '<namespace':
                            pos = 40
                            namespace = ''
                            space = True
                            while line[pos] != '>':
                                if line[pos] == ' ':
                                    space = False
                                    break
                                pos += 1
                            if space:
                                pos += 1
                                while line[pos] != '<':
                                    try:
                                        namespace += line[pos]
                                    except IndexError:
                                        print(line)
                                    pos += 1
                                namespace = namespace + ':'
                                namespaces |= {namespace}
                    except:
                        continue
            os.system("rm " + wiki + "/namespaces-" + wiki + ".txt")
            break
    print(namespaces)
    return namespaces


def try_map(page, map, current_max_id_value):
    try:
        referenced_page_id = map[page]
    except KeyError:
        current_max_id_value += 1
        map[page] = current_max_id_value
        referenced_page_id = current_max_id_value
    return referenced_page_id, map, current_max_id_value


def map_title_to_id(referenced_page_title, map, wiki_project, wiki_language, shortened, current_max_id_value, namespaces):
    '''Used to give the internal id to every page title of pages that are still in the wiki/pages-meta-history. Giving
    the original title back if its not in the map dictionary. referenced_page_title should be string with page title
    e.g. Horse and a dictionary map (preferably created by create_title_id_mapping.'''
    additionals = 0
    referenced_page_title = referenced_page_title.replace('::', ':')
    try:
        if referenced_page_title[0] == ':':
            referenced_page_title = referenced_page_title[1:]
    except:
        pass
    prefix_end = -1
    for i in range(len(referenced_page_title)):
        if referenced_page_title[i] == ':':
            prefix_end = i+1
    if 'http:' in referenced_page_title or 'https:' in referenced_page_title:
        additionals = 1
    for namespace in namespaces:
        if namespace.lower() in referenced_page_title.lower().replace('_',' '):
            additionals = 1
            referenced_page_title = (referenced_page_title[:prefix_end-len(namespace)].lower() + namespace + referenced_page_title[prefix_end:])
            break
    #if unedited:
    #    referenced_page_title = (referenced_page_title[:prefix_end].lower() + referenced_page_title[prefix_end:])
    if referenced_page_title.count(':') == (0 + additionals):
        page = wiki_project + ':' + wiki_language + ':' + referenced_page_title
        return try_map(page, map, current_max_id_value)
    elif referenced_page_title.count(':') == (1 + additionals):
        prefix = ''
        pos = 0
        while referenced_page_title[pos] != ':':
            prefix += referenced_page_title[pos]
            pos += 1
        if prefix in shortened:
            page = shortened[prefix] + ':' + wiki_language + ':' + referenced_page_title[pos+1:]
            return try_map(page, map, current_max_id_value)
        else:
            page = wiki_project + ':' + referenced_page_title
            return try_map(page, map, current_max_id_value)
    elif referenced_page_title.count(':') == (2 + additionals):
        first_prefix = ''
        second_prefix = ''
        end_first = 0
        while referenced_page_title[end_first] != ':':
            first_prefix += referenced_page_title[end_first]
            end_first += 1
        end_second = end_first + 1
        while referenced_page_title[end_second] != ':':
            second_prefix += referenced_page_title[end_second]
            end_second += 1
        if first_prefix in shortened:
            page = shortened[first_prefix] + ':' + referenced_page_title[end_first+1:]
            return try_map(page, map, current_max_id_value)
        else:
            current_max_id_value += 1
            map[referenced_page_title] = current_max_id_value
            referenced_page_id = current_max_id_value
            return referenced_page_id, map, current_max_id_value
    else:
        current_max_id_value += 1
        map[referenced_page_title] = current_max_id_value
        referenced_page_id = current_max_id_value
        return referenced_page_id, map, current_max_id_value


def edges_added(old, new):
    '''Checking for 2 lists which elements have been added.
    Not actively used since use changed from lists to sets.'''
    added = []
    for link in new:
        if link not in old:
            added.append(link)
    return added


def edges_deleted(old, new):
    '''Checking for 2 lists which elements have been deleted.
    Not actively used since use changed from lists to sets.'''
    deleted = []
    for link in old:
        if link not in new:
            deleted.append(link)
    return deleted


def create_comparable_data(title_id_map, value_map, wiki, internal, counter=0, namespaces=set()):
    '''Creating .json files for creation of nodes and creation and deletion of edges.'''
    comparable_edges = open(wiki + '/comparable_edges-' + wiki + str(counter) + '.json','w')
    textlog_nodes = open(wiki + '/textlog_nodes-' + wiki + str(counter) + '.json', 'w')
    current_timestamp = 0
    current_page_id = 0
    current_max_id_value = title_id_map[max(title_id_map, key=title_id_map.get)]
    print(current_max_id_value)
    list_of_wikis = ['wikipedia', 'wiktionary', 'wikinews', 'wikibooks', 'wikiquote', 'wikisource', 'oldwikisource',
                     'wikispecies', 'wikiversity', 'wikivoyage', 'wikimedia', 'foundation', 'commons',  'wikidata']
    shortened = {'wikipedia': 'w', 'w': 'w', 'wiktionary': 'wikt', 'wikt': 'wikt', 'wikinews': 'n', 'n': 'n',
                 'wikibooks': 'b', 'b': 'b', 'wikiquote': 'q', 'q': 'q', 'wikisource': 's', 's': 's',
                 'oldwikisource': 'oldwikisource', 'wikispecies': 'species', 'species': 'species', 'wikiversity': 'v',
                 'v': 'v', 'wikivoyage': 'voy', 'voy': 'voy', 'wikimedia': 'wmf', 'foundation': 'wmf', 'wmf': 'wmf',
                 'commons': 'c', 'c': 'c', 'wikidata': 'd', 'd': 'd', 'mediawiki': 'mw', 'mw': 'mw'}
    # The following internal links can still be added to the list but were not by us due to their non-wiki like
    # structure: 'metawikipedia', 'meta', 'incubator', 'strategy', 'mediazilla', 'bugzilla',
    # 'phabricator','testwiki', 'wikitech', 'toollabs'
    id_shift_by = value_map[wiki]
    referenced_page_title = ''
    mapping_counter = 0
    if wiki[-4:] == 'wiki':     # while normal wikis like e.g. the english wikipedia are called enwiki in filenames and
        # such they are internally referred to by their prefix enwiki -> en, dewiki -> de etc.
        # this doesnt happen to the likes of enwiktionary.
        wiki_project = 'w'
        wiki_language = wiki[:-4]
    else:
        for interwiki in list_of_wikis:
            if interwiki in wiki:
                wiki_project = shortened[interwiki]
                wiki_language = wiki[:-len(interwiki)]
    with open(wiki + '/prepareddata-' + wiki + str(counter) + '.xml') as f:
        all_edges = set()
        previous_edges = set()
        for line in f:
            if line[4:8] == '<id>':
                current_page_id = int(line[8:-6]) + id_shift_by
                page_new = True
            elif line[6:17] == '<timestamp>':
                current_timestamp = line[17:21]+line[22:24]+line[25:27]+line[28:30]+line[31:33]+line[34:36]
                if page_new:
                    textlog_nodes.write('{' + str(current_timestamp) + ', 1, ' + str(current_page_id) + ', [0]},\n')
                    page_new = False
            if line[0] == '[':      # parsing through lines that contain links and saving them to a set so comparison
                # between the old set and new set can be efficiently made and then be noted
                link_open = False
                start_pos = 0
                end_pos = 0
                for pos in range(len(line)-2):
                    if line[pos:pos+2] == '[[':
                        start_pos = pos+2
                        link_open = True
                        pos += 2
                    elif link_open and line[pos] == '|':
                        end_pos = pos-1
                    elif link_open and line[pos:pos + 2] == ']]':
                        if start_pos < end_pos:
                            referenced_page_title = line[start_pos:end_pos+1]
                        else:
                            referenced_page_title = line[start_pos:pos]
                        all_edges |= {referenced_page_title}
                        link_open = False
                    if link_open and ((line[pos:pos+5].lower() == 'file:') or (line[pos:pos + 6].lower() == 'image:')):
                        link_open = False
                if link_open:
                    if line[-2:] == ']]':
                        all_edges |= {referenced_page_title}
            if line[4:15] == '</revision>':
                if len(previous_edges) == len(all_edges):
                    if previous_edges == all_edges:
                        continue
                else:
                    added_id = []
                    for title in all_edges:
                        if len(title) > 0:
                            page_id, title_id_map, current_max_id_value = map_title_to_id(title, title_id_map,
                                                                                          wiki_project, wiki_language,
                                                                                          shortened,
                                                                                          current_max_id_value,
                                                                                          namespaces)
                            added_id.append(page_id)
                            #mapping_counter += 1
                    comparable_edges.write('{' + str(current_timestamp) + ',0,' + str(current_page_id) + ','
                                           + str(added_id) + '},\n')
                previous_edges = all_edges.copy()
                all_edges = set()
    #print(mapping_counter)
    comparable_edges.close()
    textlog_nodes.close()
    return title_id_map


def list_parsing(line, pos=0, all_edges=set()):
    while line[pos] != '[':
        pos += 1
    pos += 1
    link = ''
    while line[pos] != ']':
        if line[pos] == ' ':
            pass
        elif line[pos] == ',':
            all_edges |= {int(link)}
            link = ''
        else:
            link += line[pos]
        pos += 1
    if link != '':
        all_edges |= {int(link)}
    return all_edges


def reparse_comparable_data(wiki, counter=0):
    textlog_edges = open(wiki + '/textlog_edges-' + wiki + str(counter) + '.json', 'w')
    with open(wiki + '/comparable_edges_sorted-' + wiki + str(counter) + '.json', 'r') as comparable_edges:
        current_page_id = ''
        previous_edges = set()
        all_edges = set()
        first = False
        for revision in comparable_edges:
            try:
                timestamp = revision[1:15]
                pos = 18
                id_current_revision = ''
                while revision[pos] != ',':
                    id_current_revision += revision[pos]
                    pos += 1
                if id_current_revision != current_page_id:
                    previous_edges = set()
                    all_edges = set()
                    current_page_id = id_current_revision
                    first = True
                all_edges = list_parsing(revision, pos, all_edges)
                if first:
                    if all_edges != set():
                        textlog_edges.write('{' + str(timestamp) + ', 3, ' + str(current_page_id) + ', ['
                                            + str(all_edges)[1:-1] + ']},\n')
                        first = False
                elif len(previous_edges) == len(all_edges):
                    if previous_edges == all_edges:
                        all_edges = set()
                else:
                    added = all_edges - previous_edges  # adding an entry to the json file for both the edges which
                    # were added and the edges which were deleted
                    deleted = previous_edges - all_edges
                    if added != set():
                        textlog_edges.write('{' + str(timestamp) + ', 3, ' + str(current_page_id) + ', ['
                                            + str(added)[1:-1] + ']},\n')
                    if deleted != set():
                        textlog_edges.write('{' + str(timestamp) + ', 4, ' + str(current_page_id) + ', ['
                                            + str(deleted)[1:-1] + ']},\n')
                previous_edges = all_edges.copy()
                all_edges = set()
            except IndexError:
                continue
            except ValueError:
                continue
    textlog_edges.close()
    #os.system('rm ' + wiki + '/comparable_edges_sorted-' + wiki + str(counter) + '.json')
    return
