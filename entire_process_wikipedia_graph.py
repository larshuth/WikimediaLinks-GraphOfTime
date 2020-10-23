"""
Main file of the wikipedia graph 
"""

import time
import os
import wikipedia_pages_meta_history_download
import node_edge_timeline_creation
import pickle

def is_tool(name):
    """Check whether `name` is on PATH."""
    from distutils.spawn import find_executable
    return find_executable(name) is not None


def prepare_system():
    if is_tool("p7zip"):
        return True
    else:
        return False


def convertsize(size):
    if size/(1024**4) > 1:
        text_size = str(round(size/(1024**4), 2)) + ' TB'
    elif size/(1024**3) > 1:
        text_size = str(round(size/(1024**3), 2)) + ' GB'
    elif size/(1024**2) > 1:
        text_size = str(round(size/(1024**2), 2)) + ' MB'
    elif size/1024 > 1:
        text_size = str(round(size/1024, 2)) + ' KB'
    else:
        text_size = str(size) + ' B'
    return text_size


def size_of_data(dicts):
    total_size_all_wikis = 0
    size_per_wiki = []
    for wiki in dicts:  # Creating the dictionaries needed to map title id by parsing the files of the wikis available
        if os.path.exists(wiki + '/'):
            os.system('for f in ' + wiki + '/*.7z; do 7z l $f | tail -n 1; done > filesizes')
            total_size_wiki = 0
            with open('filesizes','r') as filesizes:
                for line in filesizes:
                    pos = 19
                    while line[pos] == ' ':
                        pos += 1
                    size = ''
                    while line[pos] != ' ':
                        size += line[pos]
                        pos += 1
                    try:
                        total_size_wiki += int(size)
                    except ValueError:
                        total_size_wiki += 0
            os.system('rm filesizes')
            total_size_all_wikis += total_size_wiki
            size_per_wiki.append([total_size_wiki, wiki])
            print(wiki + ':', total_size_wiki)
    size_per_wiki.sort(reverse=True)
    file = open('latex_table_sizes', 'w')
    file.write(r'\begin{tabular}{|lc|}'+'\n')
    file.write(r'\hline' + '\n')
    file.write(r'  Wiki & Extracted size [bytes] \\'+'\n')
    file.write(r'\hline' + '\n')
    counter = 0
    for wiki_size_combo in size_per_wiki:
        if counter == 33:
            file.write(r'\hline' + '\n')
            file.write(r'\end{tabular}\\' + '\n')
            file.write('\n')
            file.write(r'\begin{tabular}{|lc|}' + '\n')
            file.write(r'\hline' + '\n')
            file.write(r'  Wiki & Extracted size \\' + '\n')
            file.write(r'\hline' + '\n')
            counter = 0
        file.write('  ' + wiki_size_combo[1].replace('_',r'\_') + ' & ' + convertsize(wiki_size_combo[0]) + r' \\'+'\n')
        counter += 1
    file.write(r'\hline' + '\n')
    file.write(r'\end{tabular}')
    print(size_per_wiki[:5])
    print('all wikis:', str(total_size_all_wikis) + ', ' + convertsize(total_size_all_wikis))


def download_data(wikis=[]):
    '''Downloads the wikis requested.'''
    if time.localtime()[1] == 1:
        date = str(time.localtime()[0] - 1) + '1201'
    else:
        date = str(time.localtime()[0]) + str(time.localtime()[1] - 1).rjust(2, '0') + '01'
    wikipedia_pages_meta_history_download.get_wikipedia_pages_meta_history_specific_date(date, wikis)
    return


def saving_dicts_title_id(dicts):
    '''Unzip all .7z of all (chosen) wikis to a minimal degree and then creating and saving dict that maps titles to ids
    of all currently existing articles.'''
    print('Start creating title to id dict for:')
    namespaces = set()
    for wiki in dicts:    # Creating the dictionaries needed to map title id by parsing the files of the wikis available
        if os.path.exists(wiki + '/'):
            if os.path.exists('title_id_map_' + wiki + '.pkl') or os.path.exists(wiki + '/pagetitleidmap-' + wiki + '1.pkl'):
                continue
            else:
                file = open('title_id_map_' + wiki + '.pkl', 'w')
                file.write('placeholder')
                file.close()
            print(wiki)
            counter = 0
            for file in os.listdir(wiki + '/'):
                counter += 1
                print('started  ' + wiki + str(counter))
                os.system("7za e -so " + wiki + '/' + file + r" | sed -n '/^ \{4\}<title>\|^ \{4\}<id>\|^ \{6\}<namespace/p' -> " + wiki
                          + "/pagetitleidmap-" + wiki + str(counter) + ".txt")
                print('finished ' + wiki + str(counter))
            local_map, namespaces = node_edge_timeline_creation.create_title_id_mapping(wiki, namespaces)
            for file in os.listdir(wiki + '/'):
                if "pagetitleidmap-" in file:
                    os.system("rm " + wiki + '/' + file)
            print(len(local_map))
            if len(local_map) == 0:
                os.system('rm title_id_map_' + wiki + '.pkl')
                continue
            print(local_map[max(local_map, key=local_map.get)])
            node_edge_timeline_creation.save_map(local_map, wiki)
    with open('namespaces.pkl', 'wb') as file:
        pickle.dump(namespaces, file)
    return


def sort_before_final_local_graphs(wikis):
    for wiki in wikis:
        if wiki[-4:] != 'wiki':
            continue
        if os.path.exists(wiki + '/'):
            for file in os.listdir(wiki + '/'):
                if 'comparable_edges-' in file:
                    print("./wikisort_by_id " + wiki + "/" + file[:16] + '_sorted' + file[16:] + " " + wiki + "/" + file)
                    os.system("./wikisort_by_id " + wiki + "/" + file[:16] + '_sorted' + file[16:] + " " + wiki + "/" + file)
                    os.system("rm " + wiki + "/" + file)
    return


def data_processing_on_all_wikis(global_map, value_map, languages):
    '''After the wikis have been downloaded this function processes the data and creates the desired textlogs containing
    the (unsorted) information on the things happening in the graph.'''
    internal = []
    for wiki in languages:      # while normal wikis like e.g. the english wikipedia are called enwiki in filenames and
                                # such they are internally referred to by their prefix enwiki -> en, dewiki -> de etc.
                                # this doesnt happen to the likes of enwiktionary.
        if wiki[-4:] == 'wiki':
            internal.append(wiki[:-4])
        else:
            internal.append(wiki)
    if os.path.exists('namespaces.pkl'):
        namespaces_file = open('namespaces.pkl','rb')
        namespaces = pickle.load(namespaces_file)
        namespaces_file.close()
    else:
        namespaces = node_edge_timeline_creation.get_namespaces_inefficient(languages)
    for wiki in languages:
        if os.path.exists(wiki + '/'):
            counter = 0
            for file in os.listdir(wiki + '/'):
                if 'pages-meta-history' in file:
                    counter += 1
                    os.system("7za e -so " + wiki + '/' + file + r" | sed -e 's/]][^]]*$/]]/g' "
                              + r"-e 's/^[^[]*\[\[/\[\[/g' -e 's/]][^]]*\[\[\([^]]*\)]][^[]*\[\[/]]\[\[\1]]\[\[/g' | "
                              + r"sed -n '/^\[\[\|^ *</p' > " + wiki + "/prepareddata-" + wiki + str(counter) + ".xml")
                    golbal_map = node_edge_timeline_creation.create_comparable_data(global_map, value_map, wiki,
                                                                                    internal, counter, namespaces)
                    os.system("rm " + wiki + "/prepareddata-" + wiki + str(counter) + ".xml")
    sort_before_final_local_graphs(languages)
    for wiki in languages:
        if wiki[-4:] != 'wiki':
            continue
        if os.path.exists(wiki + '/'):
            counter = 0
            for file in os.listdir(wiki + '/'):
                if 'comparable_edges_sorted' in file:
                    counter += 1
                    node_edge_timeline_creation.reparse_comparable_data(wiki, counter)
    return global_map


def finish_up_textlogs(wikis):
    for wiki in wikis:
        if os.path.exists(wiki + '/'):
            files_edges = ""
            for file in os.listdir(wiki + '/'):
                if 'textlog_edges' in file:
                    files_edges += ' ' + wiki + "/" + file
            print(" ./wikisort " + wiki + "/sorted_edges_" + wiki + ".json" + files_edges)
            os.system("./wikisort " + wiki + "/sorted_edges_" + wiki + ".json" + files_edges)
            os.system("rm " + wiki + "/textlog_edges-" + wiki + "*.json")
    files_edges = ""
    for wiki in wikis:
        files_edges += " " + wiki + "/sorted_edges_" + wiki + ".json"
    os.system("./wikisort wikipedia_graph_log.json" + files_edges)
    for wiki in wikis:
        os.system("rm " + wiki + "/sorted_edges_" + wiki + ".json")
    return

def save_graph(timestamp_end='99999999999999'):
    import data_and_statistics
    graph, dict_pos_to_id, dict_id_to_pos = data_and_statistics.graph_as_list([timestamp_end])
    if timestamp_end == '99999999999999':
        file = open('wikipedia_graph_end.json', 'w')
    else:
        title = 'wikipedia_graph_' + timestamp_end + '.json'
        file = open(title, 'w')
    for pos in range(len(graph)):
        file.write(str(dict_pos_to_id[pos]) + ' ' + str(graph[pos]) + '\n')
    return


def filter_out_projects(to_be_scanned):
    output = []
    for elem in to_be_scanned:
        add = True
        for unused in ['metawiki', 'meta', 'incubator', 'strategy', 'mediawikiwiki', 'mediazilla', 'bugzilla',
                       'phabricator', 'testwiki', 'wikitech', 'toollabs', 'test', 'wikidatawiki']:
            if unused in elem.lower():
                add = False
        if add:
            output.append(elem)
    return output

def wikipedia_graph(wikis=[], dicts=[]):
    #file = open('languages.pkl','rb')
    #lang_file = pickle.load(file)
    #file.close()
    if not wikis:
        print('Get languages')
        wikis_comp = wikipedia_pages_meta_history_download.wikipedia_languages()
    else:
        wikis_comp = wikis.copy()
    if not dicts:
        dicts_comp = wikipedia_pages_meta_history_download.wikipedia_languages()
    else:
        dicts_comp = list(set(wikis) | set(dicts))

    languages = filter_out_projects(wikis_comp)
    dicts = filter_out_projects(dicts_comp)

    download_data(dicts)
    saving_dicts_title_id(dicts)
    global_map, value_map = node_edge_timeline_creation.remapping_dicts_multiple_wikis(dicts)   # combining all
                                                                                            # previously created dicts
    i_remember_what_happened_here = False
    if i_remember_what_happened_here:
        file = open('title_id_map_global_only_existing_nodes.pkl', 'rb')
        global_map = pickle.load(file)
        file.close()
        file = open('value_map.pkl', 'rb')
        value_map = pickle.load(file)
        file.close()
    print('amount key-value-pairs in wikipedia:', len(global_map))
    print('highest values:', global_map[max(global_map, key=global_map.get)])
    print(value_map)
    global_map = data_processing_on_all_wikis(global_map, value_map, languages)
    print(len(global_map))
    print(global_map[max(global_map, key=global_map.get)])
    node_edge_timeline_creation.save_map(global_map, 'global_end')
    finish_up_textlogs(wikis)
    return
