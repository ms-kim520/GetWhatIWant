import pandas as pd
import re
from datetime import datetime
from tqdm import tqdm
import numpy as np
from itertools import chain

def general_preprocess(df):
    new=df['body'].str.split('</a>',n=1,expand=True)
    df['body']=new[1]
    df['temp']=new[0]
    df['PubDate'] = df['body'].apply(lambda x : re.search(r'\d{2}\s(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s\d{4}',str(x)))
    for ix in range(len(df)):
        try:
            df['PubDate'][ix]= df['PubDate'][ix].group()
            df['PubDate'][ix]=datetime.strptime(df['PubDate'][ix],'%d %b %Y')
            df['PubDate'][ix].strftime('%Y-%m-%d')
        except:
            df['PubDate'][ix] = df['date'][ix]

    df['Source']=df['temp'].str.extract(r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})')
    df.drop(['temp'],axis=1,inplace=True)
    df['body']=df['body'].apply(lambda x : re.sub(r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})','',str(x)))
    # df['body']=df['body'].apply(lambda x : re.sub(r'[^A-Za-z0-9\s.]','',str(x)))
    return df

def chainers(s):
    return list(chain.from_iterable(s.str.split(',')))

def before_preprocess(temp):
    temp.reset_index(drop=True, inplace=True)
    temp['body'] = temp['body'].apply(lambda x:x.split('*****'))
    temp['body']=temp['body'].apply(lambda x : re.sub(r'\S*@\S*\s?','',str(x)))

    lens=temp['body'].str.split(',').map(len)
    result = pd.DataFrame({'id':np.repeat(temp['id'],lens),\
                        'keyword':np.repeat(temp['keyword'],lens),\
                        'headline':np.repeat(temp['headline'],lens),\
                        'date':np.repeat(temp['date'],lens),\
                        'body':chainers(temp['body'])})


    result['body'] = result['body'].astype(str).str.strip()
    result.reset_index(drop=True,inplace=True)

    result=result[~result['body'].str.startswith("['in this update")]
    result=result[~result['body'].str.startswith("['in this post")]
    result.reset_index(drop=True,inplace=True)
    result=general_preprocess(result)
    return result

def PreProcessing(data):
    # data = buildup(results)
    df_date=data[data['body'].str[:4]=='date']
    df_none=data[data['body'].str[:4]!='date']
    if len(df_date)>0:
        df_date.reset_index(drop=True,inplace=True)
        temp1=general_preprocess(df_date)
    else:
        temp1 = df_date
    
    if len(df_none) > 0:
        # df_none=data[data['body'].str[:4]!='date']
        temp2 = before_preprocess(df_none)
    else:
        temp2=df_none

    df = pd.concat([temp1,temp2],axis=0)
    df.reset_index(drop=True,inplace=True)
    return df
