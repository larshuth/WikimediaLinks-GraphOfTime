import os
import time


def get_latest_link():
    latest = ''
    with open('index_dates_mediatitles_wikis.html', 'r') as dates:
        for line in dates:
            if line[1] == 'a':
                latest = line[9:18]
    latest_link = "https://dumps.wikimedia.org/other/mediatitles/" + latest
    return latest_link, latest


def create_map_all_wiki_languages():
    '''Using the names of the wikis as stated in the titles of the files in the .html source of the latest
    "https://dumps.wikimedia.org/other/mediatitles/". File needs to be renamed so that the date is deleted, e.g.
    "Index of _other_mediatitles_20190625_.html" becomes "Index of other_mediatitles.html".
    Not in use now, going to be useful when combining wikipedias of multiple languages.'''
    map_languages = dict()
    with open('index_mediatitles_wikis.html') as f:
        counter = 0     # counter is going to indicate later on a maping to different page_title_id_dict for links to
                        # different language wikipedias
        for line in f:
            if line[1] == 'a':      # reference in html look like <a href = "namewiki-..." and is only there for the wikis
                end_of_name = 9
                while line[end_of_name] != '-':
                    end_of_name += 1
                map_languages[line[9:end_of_name]] = counter
                counter += 1
    return map_languages


def download_pages_meta_history_only_latest(wiki):
    '''Getting the download links to the files by parsing the html and downloading the pages-meta-history.
    The https://dumps.wikimedia.org/wiki/latest/ html have a different format compared to the html from specific dumps
    instead of latest. Therefore this is needed as its own function.'''
    counter = 0
    with open(wiki + '/dumps_wikimedia_' + wiki + '.html') as dumps:
        for line in dumps:
            if ('pages-meta-history' in line) and ('.7z"' in line):
                counter += 1
                pos = 9
                link = ''
                while line[pos] != '"':
                    link += line[pos]
                    pos += 1
                print(link)
                if link not in os.listdir(wiki + '/'):
                    os.system('wget https://dumps.wikimedia.org/' + wiki + '/latest/' + link)
                os.system('mv ' + link + ' ' + wiki + '/' + link)
    print(counter)
    return


def download_pages_meta_history(wiki):
    '''Getting the download links to the files by parsing the html and downloading the pages-meta-history.
    The https://dumps.wikimedia.org/wiki/date/ html have a different format compared to the html from the latest dump.
    Therefore this is needed as its own function.'''
    with open(wiki + '/dumps_wikimedia_' + wiki + '.html') as dumps:
        for line in dumps:
            if ('pages-meta-history' in line) and ('.7z"' in line):
                pos = 0
                while line[pos] != '"':  # the only " should be around the link if there are errors look in dumps_wikipedia_wiki
                                        # in the newest wiki folder and try to filter the downloadlinks another way.
                    pos += 1
                pos += 1
                link = ''
                print(line[pos:-2])
                while line[pos] != '"':
                    link += line[pos]
                    pos += 1
                print(link)
                counter = 0
                for i in range(len(link)):
                    if link[i] == '/':
                        counter += 1
                        if counter == 3:
                            data = link[(i + 1):]
                            print(data)
                            break
                if data not in os.listdir(wiki + '/'):
                    os.system('wget https://dumps.wikimedia.org' + link)
                print('mv ' + data + ' ' + wiki + '/' + data)
                os.system('mv ' + data + ' ' + wiki + '/' + data)
                print(data)
    return


def wikipedia_languages():
    print('Getting all wiki names.')
    os.system('wget https://dumps.wikimedia.org/other/mediatitles/')
    os.system('mv index.html index_dates_mediatitles_wikis.html')
    latest_link, latest = get_latest_link()
    os.system('rm index_dates_mediatitles_wikis.html')
    print(latest_link)
    os.system('wget ' + latest_link)
    os.system('mv index.html index_mediatitles_wikis.html')
    languages = create_map_all_wiki_languages()
    os.system('rm index_mediatitles_wikis.html')
    return languages


def get_wikipedia_pages_meta_history_latest(wikis=[]):
    '''Function downloads all of the latest pages-meta-history dumps. IMPORTANT: Function only works without fault when
    there is no dump in progress! Dumps happen from the 1st of the month onward and are usually finished by the 13/14th.
    History will not be downloaded for some wikis so in case of doubt start a few days/weeks later or look at
    https://dumps.wikimedia.org/backup-index-bydb.html to make sure no dump is in progress anymore. Using the
    specific_date function is recommended.'''
    if wikis == []:
        languages = wikipedia_languages()
    else:
        languages = wikis
    for wiki in languages:
        if not os.path.exists(wiki + '/'):
            os.system('mkdir ' + wiki)
        print(wiki)
        os.system('wget https://dumps.wikimedia.org/' + wiki + '/latest/')
        os.system('mv index.html ' + wiki + '/dumps_wikimedia_' + wiki + '.html')
        download_pages_meta_history_only_latest(wiki)
        print(wiki + ' finished')
    print('wikipedia finished')
    return

def get_wikipedia_pages_meta_history_specific_date(date, wikis = []):
    '''Function returns (if available) the pages-meta-history from the specific date. Date has to be a string in the
    format "yyyymmdd" since the dump is always dated to the 1st the function will get the previous dump if available.
    Dumps are usually only available for the last 4 months (for big wikis like the enwiki only 3 months).'''
    if wikis == []:
        languages = wikipedia_languages()
    else:
        languages = wikis
    if date[6:] != '01':
        date = date[:6] + '01'
    #os.system('mkdir wikipedia_' + date)
    for wiki in languages:
        print(wiki)
        if not os.path.exists(wiki + '/'):
            os.system('mkdir ' + wiki)
        os.system('wget https://dumps.wikimedia.org/' + wiki + '/' + date + '/')
        os.system('mv index.html ' + wiki + '/dumps_wikimedia_' + wiki + '.html')
        download_pages_meta_history(wiki)
        os.system('rm ' + wiki + '/dumps_wikimedia_' + wiki + '.html')
        print(wiki + ' finished')
    os.system('rmdir *')
    print('wikipedia finished')
    return


def get_wikipedia_pages_meta_history_oldest_available(wikis = []):
    if wikis == []:
        languages = wikipedia_languages()
    else:
        languages = wikis
    for wiki in languages:
        print(wiki)
        if not os.path.exists('wiki/'):
            os.system('mkdir ' + wiki)
        os.system('wget https://dumps.wikimedia.org/' + wiki + '/')
        os.system('mv index.html ' + wiki + '/dumps_wikimedia_' + wiki + '.html')
        with open(wiki + '/dumps_wikimedia_' + wiki + '.html','r') as dates:
            for line in dates:
                if (line[1] == 'a') and (line[15:17] == '01'):  # IMPORTANT! As of writing the dumps always happen on
                                                                # the 1st and the 20th. pages-meta-history is only being
                                                                # dumped on the 1st (therefore searching for the 01)
                    oldest_date = line[9:17]
                    break
        print(oldest_date)
        os.system('wget https://dumps.wikimedia.org/' + wiki + '/' + oldest_date + '/')
        os.system('mv index.html ' + wiki + '/dumps_wikimedia_' + wiki + '.html')
        download_pages_meta_history(wiki)
        os.system('rm ' + wiki + '/dumps_wikimedia_' + wiki + '.html')
        print(wiki + ' finished')
    os.system('rmdir *')
    print('wikipedia finished')
    return


#get_wikipedia_latest()
#get_wikipedia_pages_meta_history_oldest_available()
