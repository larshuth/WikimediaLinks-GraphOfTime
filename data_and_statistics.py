import wikipedia_pages_meta_history_download
import entire_process_wikipedia_graph
import node_edge_timeline_creation
import matplotlib.pyplot as plt
import os
import pickle
from datetime import datetime

plt.rcParams.update({'font.size': 14})

def statistical_values_of_list(values):
    values.sort()
    if len(values) != 0:
        mean = sum(values) / len(values)
        if len(values) % 2 == 1:
            median = values[int(len(values) / 2)]
        else:
            median = (values[int((len(values) / 2) - 0.5)] + values[int((len(values) / 2) + 0.5)]) / 2
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return mean, median, variance
    else:
        return 0, 0, 0


def cut_away_outliers(data, z=0.0001):
    sum_of_datapoints = sum(data)
    highest_z_percent = 0
    pos = len(data) - 1
    while pos > 0:
        highest_z_percent += data[pos]
        if sum_of_datapoints * z < highest_z_percent:
            break
        pos -= 1
    return pos


def check_unsorted_data():
    total_edges_over_time = 0
    total_edges_deleted_over_time = 0
    total_edges_added_over_time = 0
    with open('wikipedia_graph.json', 'r') as file:
        for line in file:
            try:
                changes = line.count(',') - 3
                if line[16] == '3':
                    total_edges_over_time += changes
                    total_edges_added_over_time += changes
                elif line[16] == '4':
                    total_edges_over_time -= changes
                    total_edges_deleted_over_time += changes
            except:
                print('error?')
    print(total_edges_over_time)
    print(total_edges_added_over_time)
    print(total_edges_deleted_over_time)
    return



def calc_degree_correlation(graph, dict_id_to_pos, max_known):
    graph_only_working = [(set([edge if edge <= max_known else 0 for edge in edges]) - {0}) for edges in graph]
    #print(dict_id_to_pos)
    degree_correlation = []
    unknown = []
    highest_degree = max([len(v) for v in graph_only_working])
    #print(highest_degree)
    for i in range(highest_degree + 1):
        degree_correlation.append([])
        unknown.append(0)
        for j in range(highest_degree + 1):
            degree_correlation[-1].append(0)
    #print(degree_correlation)
    seen_edges = 0
    for edges in graph_only_working:
        for edge in edges:
            if edge <= max_known:
                try:
                    degree_correlation[len(edges)][len(graph_only_working[dict_id_to_pos[str(edge)]])] += 1
                except KeyError:
                    degree_correlation[len(edges)][0] += 1
            else:
                unknown[len(edges)] += 1
            seen_edges += 1
    #print('länge degree correlation:', len(degree_correlation))
    total = sum([sum(d) for d in degree_correlation])
    #print('menge kanten in degree correlation:', total)
    #print('kantenziele mit unbekanntem aus-grad:', sum(unknown))
    #print('gesamt gezählte kanten:', seen_edges)
    for i in range(len(degree_correlation)):
        total_local = sum(degree_correlation[i])
        if total_local != 0:
            for target_size in range(len(degree_correlation)):
                degree_correlation[i][target_size] /= total_local
            unknown[i] /= total_local
        else:
            for target_size in range(len(degree_correlation)):
                degree_correlation[i][target_size] = 0.0
            unknown[i] = 0.0
    return degree_correlation, unknown


def distribution_edges_per_node(graph):
    distribution = []
    for node in graph:
        try:
            distribution[len(node)] += 1
        except IndexError:
            for i in range(len(node) - len(distribution)):
                distribution.append(0)
            distribution.append(1)
    total = sum(distribution)
    for i in range(len(distribution)):
        distribution[i]# /= total
    return distribution


def amount_broken_links(graph, max_known):
    number_broken_links = [len(set([edge if edge > max_known else 0 for edge in edges]) - {0}) for edges in graph]
    percentile_broken_links = []
    for i in range(len(graph)):
        if len(graph[i]) != 0:
            percentile_broken_links.append(number_broken_links[i]/len(graph[i]))
        else:
            percentile_broken_links.append(0)
    return number_broken_links, percentile_broken_links


def table_where_do_links_lead(graph, max_known, dict_pos_to_id):
    file = open('value_map.pkl', 'rb')
    value_map = pickle.load(file)
    file.close()
    dicts = [wiki for wiki in value_map]
    old_values = []
    link_table = []
    for i in range(len(dicts)):
        old_values.append([])
        try:
            old_values[i].append(value_map[dicts[i+1]])
            old_values[i].append(dicts[i])
        except IndexError:
            old_values[i].append(max_known+1)
            old_values[i].append(dicts[i])
        link_table.append([])
        for j in range(len(dicts)):
            link_table[i].append(0)
        link_table[i].append(0)
    if sum([len(v) for v in graph]) == 0:
        return [], []
    old_values.sort()
    source = ''
    for pos_in_graph in range(len(graph)):
        for i in range(len(old_values)):
            if int(dict_pos_to_id[pos_in_graph]) < old_values[i][0]:
                source = i
                break
        for id_target in graph[pos_in_graph]:
            for i in range(len(old_values)):
                if id_target < old_values[i][0]:
                    link_table[source][i] += 1
                    break
            link_table[source][-1] += 1
    all_removed = False
    while not all_removed:
        all_removed = True
        for wiki in range(len(link_table)):
            if sum(link_table[wiki]) == 0:
                #print(link_table, '-', wiki)
                link_table = link_table[:wiki] + link_table[wiki+1:]
                dicts = dicts[:wiki] + dicts[wiki+1:]
                all_removed = False
                break
    #print(link_table)
    #print(dicts)
    #print('made it')
    return link_table, old_values


def graph_as_list(timestamp_end=['99999999999999'], statistics=False, max_known=0):
    timestamp_pos = 0
    timestamp = ''
    graph = []
    snapshots = []
    distributions_edges = []
    boxplots_broken_links = []
    tables_over_time = []
    known_edges_over_time = [0]
    unknown_edges_over_time = [0]
    timestamps = []
    if max_known == 0:
        file = open('title_id_map_global_only_existing_nodes.pkl', 'rb')
        title_id_map = pickle.load(file)
        max_known = title_id_map[max(title_id_map, key=title_id_map.get)]
        file.close()
        title_id_map = set()
    dict_id_to_pos = dict()
    dict_pos_to_id = dict()
    print('start file')
    with open('wikipedia_graph_log.json', 'r') as complete_log_of_changes:
        for line in complete_log_of_changes:
            if timestamp > timestamp_end[-1]:
                break
            try:
                timestamp = line[1:15]
                #if line[1:9] < '20130101' or line[1:9] > '20140101':
                #    continue
                if timestamp > timestamp_end[timestamp_pos]:
                    if statistics:
                        #print('snapshot', timestamp_end[timestamp_pos], 'start')
                        snapshots.append([len(g) for g in graph])
                        distributions_edges.append(distribution_edges_per_node(graph))
                        try:
                            boxplots_broken_links.append(amount_broken_links(graph, max_known))
                        except IndexError:
                            boxplots_broken_links.append(0, 0)
                        #tables_over_time.append(table_where_do_links_lead(graph, max_known, dict_pos_to_id))
                        print('snapshot', timestamp_end[timestamp_pos], 'finished')
                    timestamp_pos += 1
                pos = 18
                current_id = ''
                while line[pos] != ',':
                    current_id += line[pos]
                    pos += 1
                if not current_id in dict_id_to_pos:
                    dict_id_to_pos[current_id] = len(dict_id_to_pos)
                    dict_pos_to_id[len(dict_pos_to_id)] = current_id
                    graph.append(set())
                while line[pos] != '[':
                    pos += 1
                pos += 1
                link = ''
                changed_links = set()
                while line[pos] != ']':
                    if line[pos] == ' ':
                        pass
                    elif line[pos] == ',':
                        changed_links |= {int(link)}
                        link = ''
                    else:
                        link += line[pos]
                    pos += 1
                if link != '':
                    changed_links |= {int(link)}
                if line[16] == '3':
                    graph[dict_id_to_pos[current_id]] |= changed_links
                    if statistics:
                        known = 0
                        unknown = 0
                        for page_id in changed_links:
                            if page_id <= max_known:
                                known += 1
                            else:
                                unknown += 1
                        known_edges_over_time.append(known_edges_over_time[-1] + known)
                        unknown_edges_over_time.append(unknown_edges_over_time[-1] + unknown)
                elif line[16] == '4':
                    graph[dict_id_to_pos[current_id]] -= changed_links
                    if statistics:
                        known = 0
                        unknown = 0
                        for page_id in changed_links:
                            if page_id <= max_known:
                                known += 1
                            else:
                                unknown += 1
                        known_edges_over_time.append(known_edges_over_time[-1] - known)
                        unknown_edges_over_time.append(unknown_edges_over_time[-1] - unknown)
                else:
                    print('Error')
                    break
                timestamps.append(timestamp)
            except IndexError:
                print('IndexError')
                continue
            except ValueError:
                print('ValueError')
    print('Graph länge:', len(graph))
    print('Anzahl Kanten:', sum([len(v) for v in graph]))
    known_edges_over_time = known_edges_over_time[1:]
    unknown_edges_over_time = unknown_edges_over_time[1:]
    snapshots.append([len(g) for g in graph])
    distributions_edges.append(distribution_edges_per_node(graph))
    if statistics:
        #print(tables_over_time[-1])
        #degree_correlation, unknown_per_out_degree = calc_degree_correlation(graph, dict_id_to_pos, max_known)
        return snapshots, distributions_edges, unknown_edges_over_time, known_edges_over_time, timestamps,\
               boxplots_broken_links#, tables_over_time#, unknown_per_out_degree, degree_correlation,
    return graph, dict_pos_to_id, dict_id_to_pos


def statistics_over_time():
    file = open('title_id_map_global_only_existing_nodes.pkl', 'rb')
    title_id_map = pickle.load(file)
    max_known = title_id_map[max(title_id_map, key=title_id_map.get)]
    file.close()
    title_id_map = set()
    file = open('value_map.pkl', 'rb')
    value_map = pickle.load(file)
    file.close()
    dicts = [wiki for wiki in value_map]
    old_values = []
    for i in range(len(dicts)):
        old_values.append([])
        try:
            old_values[i].append(value_map[dicts[i+1]])
            old_values[i].append(dicts[i])
        except IndexError:
            old_values[i].append(max_known+1)
            old_values[i].append(dicts[i])
    old_values.sort()
    dates = ['0000-00-00']
    all_nodes = set()
    node_add_timestamp = ['00000000000000']
    total_nodes_over_time = [0]
    total_edges_over_time = [0]
    total_edges_deleted_over_time = [0]
    total_edges_added_over_time = [0]
    average_edges_per_node = [0]
    timestamp_edge = ''
    timestamp_node = ''
    time = '000000'
    languages = wikipedia_pages_meta_history_download.wikipedia_languages()
    for wiki in languages:
        if wiki[-4:] != 'wiki':
            continue
        if os.path.exists(wiki + '/'):
            for file in os.listdir(wiki + '/'):
                if 'textlog_nodes' in file:
                    with open(wiki + '/' + file) as nodes:
                        for line in nodes:
                            node_add_timestamp.append(line[1:15])
    node_add_timestamp.sort()
    position_node = 0
    error_counter = 0
    with open('wikipedia_graph_log.json', 'r') as file:
        for line in file:
            try:
                if line[0] == '[' or line[0] == ']' :
                    continue
                #if timestamp_edge != line[1:9]:
                timestamp_edge = line[1:9]
                if line[1:7] > time:
                    time = line[1:7]
                    print(time[:4] + '-' + time[4:])
                    #if timestamp_edge < '20130101' or timestamp_edge > '20140101':
                    #    continue
                pos = 18
                current_id = ''
                while line[pos] != ',':
                    current_id += line[pos]
                    pos += 1
                if not int(current_id) in all_nodes:
                    all_nodes |= {int(current_id)}
                    total_nodes_over_time[-1] += 1
                    average_edges_per_node[-1] = (total_edges_over_time[-1] / total_nodes_over_time[-1])
                if dates[-1] != timestamp_edge[0:4] + '-' + timestamp_edge[4:6] + '-' + timestamp_edge[6:8]:
                    dates.append(line[1:5] + '-' + line[5:7] + '-' + line[7:9])
                    #if len(dates) > 2:
                    #    break
                    total_nodes_over_time.append(total_nodes_over_time[-1])
                    total_edges_over_time.append(total_edges_over_time[-1])
                    total_edges_deleted_over_time.append(total_edges_deleted_over_time[-1])
                    total_edges_added_over_time.append(total_edges_added_over_time[-1])
                    average_edges_per_node.append(total_edges_over_time[-1] / total_nodes_over_time[-1])
                changes = line.count(',') - 3
                if line[16] == '3':
                    total_edges_over_time[-1] += changes
                    total_edges_added_over_time[-1] += changes
                    average_edges_per_node[-1] = (total_edges_over_time[-1] / total_nodes_over_time[-1])
                elif line[16] == '4':
                    total_edges_over_time[-1] -= changes
                    total_edges_deleted_over_time[-1] += changes
                    average_edges_per_node[-1] = (total_edges_over_time[-1] / total_nodes_over_time[-1])
                #print(timestamp_edge, total_edges_over_time[-1])
            except IndexError:
                error_counter += 1
                print('IndexError')
                print(line)
                if error_counter > 4:
                    return
                else:
                    continue
            except ZeroDivisionError:
                print(ZeroDivisionError)
                print(dates)
                print(total_nodes_over_time)
                print(total_edges_over_time)
                print(line)
                return
    print(dates[-5:])
    print(total_nodes_over_time[-5:])
    #print(all_nodes)
    print(len(all_nodes))
    total_edges_over_time = total_edges_over_time[1:]
    total_edges_added_over_time = total_edges_added_over_time[1:]
    total_edges_deleted_over_time = total_edges_deleted_over_time[1:]
    total_nodes_over_time = total_nodes_over_time[1:]
    average_edges_per_node = average_edges_per_node[1:]
    dates = dates[1:]

    print('len total_edges_over_time', len(total_edges_over_time))
    print('len total_edges_added_over_time', len(total_edges_added_over_time))
    print('len total_edges_deleted_over_time', len(total_edges_deleted_over_time))
    print('len total_nodes_over_time', len(total_nodes_over_time))
    print('len dates', len(dates))
    print('len node_add_timestamp', len(node_add_timestamp))
    print('edges at end d_a_s', total_edges_over_time[-1])
    dates = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

    plt.figure(figsize=(7, 7), dpi=300)
    plt.plot(dates, total_edges_over_time, label='amount edges at the time')
    plt.plot(dates, total_edges_deleted_over_time, color='r', label='total amount deleted edges')
    plt.plot(dates, total_edges_added_over_time, color='g', label='total amount added edges')
    #plt.set_title('Amount of edges over time:\n green = total added\nred = total deleted\n
    # blue = amount edges at point of time')
    plt.legend(loc='upper left')
    plt.savefig('edges_over_time.png')
    plt.close()

    plt.figure(figsize=(7, 7), dpi=300)
    fig1, ax1 = plt.subplots()
    plt.plot(dates, average_edges_per_node, color='b', label='average out-degree')
    mean, median, variance = statistical_values_of_list(average_edges_per_node.copy())
    plt.text(1, 0.9, 'Average out-degree:\nmean: '+str(round(mean, 2))+'\nmedian: '+str(round(median, 2))+\
             '\nvariance: '+str(round(variance, 2)), {'color': 'C2', 'fontsize': 18}, va="top", ha="right")
    #plt.legend(loc='upper left')
    ax1.set_title('Average out-degree')
    plt.savefig('average_out-degree.png')
    plt.close()

    plt.figure(figsize=(7, 7), dpi=300)
    fig1, ax1 = plt.subplots()
    ax1.set_title('Number of nodes')
    plt.plot(dates, total_nodes_over_time, color='g', label='amount nodes')
    plt.savefig('amount_nodes.png')
    plt.close()

    total_edges_over_time = []
    #total_edges_added_over_time = []
    #total_edges_deleted_over_time = []
    total_nodes_over_time = total_nodes_over_time[-1]
    average_edges_per_node = []
    dates = dates[0:2]
    print(dates)

    snapshots_timestamps = []
    for i in range(int(str(dates[0])[:4]), 2020):
        if i == int(str(dates[0])[:4]):
            if 7 <= int(str(dates[0])[4:6]):
                snapshots_timestamps.append(str(i) + '0701000000')
            else:
                snapshots_timestamps.append(str(i) + '0101000000')
                snapshots_timestamps.append(str(i) + '0701000000')
        else:
            snapshots_timestamps.append(str(i) + '0101000000')
            snapshots_timestamps.append(str(i) + '0701000000')
    snapshots_timestamps.append('99999999999999')
    print('start snapshots')
    snapshots, distributions, unknown_edges_over_time, known_edges_over_time, un_known_timestamps, \
    boxplots_broken_links = graph_as_list(snapshots_timestamps, True, max_known)
    #, tables_over_time  degree_correlation, unknown_per_out_degree,
    print('end snapshots')
    snapshots_timestamps = snapshots_timestamps[:-1] + ['20190801000000']

    snapshots_timestamps_datetime = [datetime.strptime(d[:4] + '-' + d[4:6] + '-' + d[6:8], '%Y-%m-%d')
                            for d in snapshots_timestamps]
    #un_known_timestamps = [datetime.strptime(t[:4] + '-' + t[4:6] + '-' + t[6:8] + '-' + t[8:10] + '-' + t[10:12] +
    #                                         '-' + t[12:14], '%Y-%m-%d-%H-%M-%S') for t in un_known_timestamps]

    special_snapshots_timestamps = [float(d[:4]+'.'+d[4:6]) for d in snapshots_timestamps]
    print(len(special_snapshots_timestamps))
    print(len(snapshots))
    print(len(boxplots_broken_links))

    plt.figure(figsize=(16.54, 11.69), dpi=300)
    fig1, ax1 = plt.subplots()
    ax1.set_title('Edges per node')
    ax1.boxplot(snapshots)#, positions=special_snapshots_timestamps)
    ax1.semilogy()
    plt.savefig('boxplots_of_edges_per_node.png')
    plt.close()
    print('boxplots_of_edges_per_node.png')

    special_snapshots_timestamps = special_snapshots_timestamps[:-1]

    plt.figure(figsize=(16.54, 11.69), dpi=300)
    fig1, ax1 = plt.subplots()
    ax1.set_title('Amount broken links per page [%]')
    ax1.boxplot([i[1] for i in boxplots_broken_links])#, positions=special_snapshots_timestamps)
    plt.savefig('boxplots_broken_links_percentile.png')
    plt.close()
    print('boxplots_broken_links_percentile.png')

    plt.figure(figsize=(16.54, 11.69), dpi=300)
    fig1, ax1 = plt.subplots()
    ax1.set_title('Amount broken links per page [total]')
    ax1.boxplot([i[0] for i in boxplots_broken_links])#, positions=special_snapshots_timestamps)
    ax1.semilogy()
    plt.savefig('boxplots_broken_links_absolute.png')
    plt.close()
    print('boxplots_broken_links_absolute.png')

    #snapshots_timestamps_datetime = snapshots_timestamps_datetime[:-1]

    percent_of_pages_less_than_ten_links = []
    for dist in distributions:
        total_dist = sum(dist)
        cummulative = 0
        if len(dist) < 11:
            percent_of_pages_less_than_ten_links.append(1)
            continue
        for i in range(10):
            cummulative += (dist[i]/total_dist)
        percent_of_pages_less_than_ten_links.append(cummulative)
    fig1, ax1 = plt.subplots()
    ax1.set_title('Percentage Nodes with Out-Degree < 11')
    plt.plot(snapshots_timestamps_datetime, percent_of_pages_less_than_ten_links, color='g')
    plt.savefig('degree_less_than_ten.png')
    plt.close()
    print('degree_less_than_ten.png')
    
    counter = 0
    for dist in distributions:
        counter += 1
        total_dist = sum(dist)
        #dist = dist[:cut_away_outliers(dist, 0.05)]
        plt.figure(figsize=(7, 7), dpi=300)
        fig, ax1 = plt.subplots()
        ax1.set_title(str(snapshots_timestamps_datetime[counter-1])[:10]+' - ' + str(total_dist) + ' nodes')
        plt.loglog()
        plt.plot(range(len(dist)), [(d/total_dist) for d in dist])
        plt.savefig('distributions_of_edges_per_node' + str(snapshots_timestamps_datetime[counter-1])[:10].replace('-', '_') + '.png')
        plt.close()
        print('distributions_of_edges_per_node' + str(snapshots_timestamps_datetime[counter-1])[:10].replace('-', '_') + '.png')

    '''
    total_edges_un_known = [unknown_edges_over_time[i] + known_edges_over_time[i] for i in range(len(unknown_edges_over_time))]
    plt.plot(un_known_timestamps, total_edges_un_known, label='amount edges')
    plt.plot(un_known_timestamps, unknown_edges_over_time, color='r', label='amount edges unknown target')
    plt.plot(un_known_timestamps, known_edges_over_time, color='g', label='amount edges at the time known target')
    # plt.set_title('Amount of edges over time: known (green) vs unknown (red) vs total (blue)')
    plt.legend(loc='upper left')
    plt.savefig('edges_known_vs_unknown.png')
    plt.close()
    print('edges_known_vs_unknown.png')
    '''
    print(total_edges_added_over_time[-1], total_edges_deleted_over_time[-1])
    print(total_nodes_over_time)
    return


def statistics_unregarding_of_time():
    '''These statistics take a look at the at the number of changes that happened to edges not regarding time it
    happened at.'''
    amount_of_times_edges_added = [0]
    amount_of_times_edges_deleted = [0]
    timestamp = ''
    added = True
    deleted = True
    with open('wikipedia_graph_log.json', 'r') as file:
        for line in file:
            try:
                if timestamp != line[1:15]:
                    timestamp = line[1:15]
                    if not added:
                        amount_of_times_edges_added[0] += 1
                    if not deleted:
                        amount_of_times_edges_deleted[0] += 1
                    added = False
                    deleted = False
                changes = line.count(',') - 3
                #if changes > 50:
                #    continue
                if line[16] == '3':
                    try:
                        amount_of_times_edges_added[changes] += 1
                        added = True
                    except IndexError:
                        for i in range(changes - len(amount_of_times_edges_added)):
                            amount_of_times_edges_added.append(0)
                        amount_of_times_edges_added.append(1)
                        added = True
                else:
                    try:
                        amount_of_times_edges_deleted[changes] += 1
                        deleted = True
                    except IndexError:
                        for i in range(changes - len(amount_of_times_edges_deleted)):
                            amount_of_times_edges_deleted.append(0)
                        amount_of_times_edges_deleted.append(1)
                        deleted = True
            except:
                continue
    # Since there are a few outliers in the data e.g. 14000 edges added to a page in the Kannadan (Southernwest India)
    # Wikipedia the data will be cut here to not include the z percent of highest edge changes
    z = 0.001       # 0.001 = 0.01% -> 99.99% or the data will be used

    pos = cut_away_outliers(amount_of_times_edges_added, z)
    amount_of_times_edges_added = amount_of_times_edges_added[:pos]

    pos = cut_away_outliers(amount_of_times_edges_deleted, z)
    amount_of_times_edges_deleted = amount_of_times_edges_deleted[:pos]

    edges_total_added = 0
    edges_total_deleted = 0
    test_adding = []
    test_deleting = []

    for i in range(len(amount_of_times_edges_added)):
        edges_total_added += (amount_of_times_edges_added[i] * i)
        test_adding.append(edges_total_added)

    for i in range(len(amount_of_times_edges_deleted)):
        edges_total_deleted += (amount_of_times_edges_deleted[i] * i)
        test_deleting.append(edges_total_deleted)

    edges_at_the_end = edges_total_added - edges_total_deleted
    visualize_adding_total(amount_of_times_edges_added)
    visualize_deleting_total(amount_of_times_edges_deleted)
    visualize_adding_percental_accumulated(amount_of_times_edges_added, edges_total_added)
    visualize_deleting_percental_accumulated(amount_of_times_edges_deleted, edges_total_deleted)
    whatever_the_frick_you_call_this_total_add(amount_of_times_edges_added)
    whatever_the_frick_you_call_this_total_del(amount_of_times_edges_deleted)
    return


def visualize_adding_total(amount_of_times_edges_added):
    '''Amount of times a specific amount of edges is added in a revision, only counting revision that that contain any
    changes to the edges.'''
    plt.plot(range(len(amount_of_times_edges_added)), amount_of_times_edges_added, color='g')
    plt.yscale('log')
    plt.savefig('amount_edges_added_per_revision_that_includes_edge_changes.png')
    plt.close()
    return


def visualize_deleting_total(amount_of_times_edges_deleted):
    '''Amount of times a specific amount of edges is deleted in a revision, only counting revision that that contain any
    changes to the edges.'''
    plt.plot(range(len(amount_of_times_edges_deleted)), amount_of_times_edges_deleted, color='r')
    plt.yscale('log')
    plt.savefig('amount_edges_deleted_per_revision_that_includes_edge_changes.png')
    plt.close()
    return


def whatever_the_frick_you_call_this_total_add(amount_of_times_edges_added):
    '''Total amount of edges that are added during all revisions with the same amount of edge adds, only counting
    revision that that contain any changes to the edges.'''
    for i in range(len(amount_of_times_edges_added)):
        amount_of_times_edges_added[i] *= i
    plt.plot(range(len(amount_of_times_edges_added)), amount_of_times_edges_added, color='g')
    #plt.yscale('log')
    plt.savefig('frick_added.png')
    plt.close()
    return


def whatever_the_frick_you_call_this_total_del(amount_of_times_edges_deleted):
    '''Total amount of edges that are deleted during all revisions with the same amount of edge adds, only counting
    revision that that contain any changes to the edges.'''
    for i in range(len(amount_of_times_edges_deleted)):
        amount_of_times_edges_deleted[i] *= i
    plt.plot(range(len(amount_of_times_edges_deleted)), amount_of_times_edges_deleted, color='g')
    plt.yscale('log')
    #plt.savefig('frick_deleted.png')
    plt.close()
    return


def visualize_adding_percental_accumulated(amount_of_times_edges_added, edges_total_added):
    '''Percentwise how many times have changes happened with this much or less active edge changes'''
    sum_added = sum(amount_of_times_edges_added)
    percents = []
    progress = 0
    for change in amount_of_times_edges_added:
        progress += change
        percents.append(progress/sum_added)
    #print(percents)

    plt.plot(range(len(percents)), percents, color='g')

    #print(edges_total_added)
    percents = []
    progress = 0
    for i in range(len(amount_of_times_edges_added)):
        progress += amount_of_times_edges_added[i] * i
        percents.append(progress/edges_total_added)
        #print(amount_of_times_edges_added[i] * i)
    #print(percents)

    plt.plot(range(len(percents)), percents, color='b')

    plt.axhline(y=1, xmin=0, color='r')
    plt.savefig('added_percental_accumulated_total_added.png')
    plt.close()
    return


def visualize_deleting_percental_accumulated(amount_of_times_edges_deleted, edges_total_deleted):
    sum_deleted = sum(amount_of_times_edges_deleted)
    percents = []
    progress = 0
    for change in amount_of_times_edges_deleted:
        progress += change
        percents.append(progress/sum_deleted)

    plt.plot(range(len(amount_of_times_edges_deleted)), percents, color='g')

    percents = []
    progress = 0
    for i in range(len(amount_of_times_edges_deleted)):
        progress += amount_of_times_edges_deleted[i] * i
        percents.append(progress / edges_total_deleted)

    plt.plot(range(len(amount_of_times_edges_deleted)), percents, color='b')

    plt.axhline(y=1, xmin=0, color='r')
    plt.savefig('deleted_percental_accumulated_total_deleted.png')
    plt.close()
    return
