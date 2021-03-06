# -*- coding: utf-8 -*-
"""
Creates pool which grabs data from wayback machine for sites for specific date
Iterates date and repeats, saving to disk as csv file
Note: newspaper3k MUST be edited to NOT cache articles!
      It will use cnn's cache for fox and vice versa.
"""

from datetime import date, timedelta
from tqdm import tqdm
import newspaper
import pandas as pd
import multiprocessing as mp
import re
import time
import random

PROCESS_COUNT = 16
ARCHIVE_MAX = 4

def grab_and_save(url, date, bias, archive_max):
    # grab articles from archive without memoization for continuity
    try:
        # only let 4 processes use the archive at once
        while archive_max.value > ARCHIVE_MAX:
            time.sleep(random.uniform(0.5, 3.0))
        archive_max.value += 1
        
        # try to find articles on wayback machine
        check = 'https://web.archive.org/web/' + date + 'id_/https://' + url
        paper=newspaper.build(check,memoize_articles=False,fetch_images=False,
                              follow_meta_refresh=True,keep_article_html=False)
        
        # release the archive
        archive_max.value -= 1
        
        # replace archived articles with source's articles
        for a in paper.articles:
            a.url = a.url[-a.url[::-1].index('ptth')-4:]
            
        # download and parse
        paper.download_articles(threads=2)
        paper.parse_articles()
    
    except Exception as e:
        print(e)
        print('Skipped site: ' + str(url))
        return
    
    # appending data to list
    records = list()
    for article in paper.articles:
        try:
            records.append([re.sub('\s+', ' ', article.text),   # content
                          str(article.publish_date),            # date
                          article.authors,                      # authors
                          article.url,                          # url
                          url,                                  # source
                          article.title,                        # title
                          bias])                                # bias
    
        except Exception as e:
            print(e)
            print('Skipped: ' + str(article.url))
    
    # return list of records
    return records

if __name__ == '__main__':
    # sites df shows which sites to target
    sites = pd.read_csv('outlet_bias.csv', index_col='Unnamed: 0')
    
    # date information
    cur_date = date.today()
    end_date = date(2011, 12, 31)
    delta = timedelta(days=1)
    
    # create a file to write to
    pd.DataFrame(columns=['content','date','authors','url',\
        'source','title','label']).to_csv('daily_data.csv')
    
    # max amount of processes allowed to use the archive at once
    manager = mp.Manager()
    archive_max = manager.Value('i', 0)
    
    # loop through dates
    pbar = tqdm(total=(cur_date - end_date).days, desc=str(cur_date))
    while cur_date > end_date:
        # date string
        tmp_date = cur_date.strftime("%Y%m%d")
        
        # pool for grabbing site data
        with mp.Pool(PROCESS_COUNT) as p:
            results = [p.apply_async(grab_and_save, (url, tmp_date, bias, \
                archive_max,)) for url, bias in zip(sites.url, sites.bias)]
            p.close()
            p.join()
        
        # write records from process results to disk
        with open('daily_data.csv', 'a') as file:
            for res in results:
                file.write('\n'.join(','.join(record) for record in res))
                if results:
                    file.write('\n')
        
        # update cur_date
        cur_date -= delta
        pbar.set_description(str(cur_date))
        pbar.update(delta.days)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    