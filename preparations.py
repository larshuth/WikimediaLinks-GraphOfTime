import pickle
import latest_wikipedia_pages_meta_history_download_script as wowy
import os
file = open('languages-pkl', 'wb')
pickle.dump(wowy.wikipadia_languages(), file)
os.system('scp languages.pkl huth@goethe.hhlr-gu.de:/scratch/memhierarchy/huth/wikipedia_20190301_pages_meta_history/language.pkl')
