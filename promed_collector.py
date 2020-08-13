import time
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import json
from tqdm.notebook import tqdm
import datetime
import re
import warnings
warnings.filterwarnings(action='ignore')


#가지고 와야 할 각 링크의 아이디를 담는 리스트 만들기
def get_id(results,keyword):
    temp= []
    for index,res in enumerate(results):
        if res=='i' and results[index+1]=='d' and results[index+2].isdigit():
            temp.append((keyword,results[index+2:index+9])) 
    return temp

#ProMED에서 시작날짜, 끝 날짜 정해서 전체 화면 및 아이디들 들고 오기
def get_All_link_proMED(headers,start,end,keyword=None):
    id_list=[]
    #시작 날짜와 끝 날짜를 넣고 search까지 누른 후의 전체 화면 가지고 오기 50건의 결과
    params = {"action": "get_promed_search_content","query[0][name]": "kwby1","query[0][value]": "summary",\
        "query[1][name]": "search","query[1][value]": {keyword},"query[2][name]":"date1","query[2][value]":{start},\
             "query[3][name]":"date2","query[3][value]":{end}, "query[4][name]": "feed_id","query[4][value]": "1"} 
    req = requests.post("https://promedmail.org/wp-admin/admin-ajax.php",headers=headers,data=params)
    cnt=req.json()['res_count']
    results=req.json()['results']
    
    #전체 결과 수가 50을 넘으면 여러번 next를 해서 결과를 가지고 와야 함
    if cnt>50:
        page=round(cnt/50)
        i=0
        while i<page:
            params_next={"action": "get_promed_search_content","query[0][name]": "pagenum","query[0][value]": str(i+1),"query[1][name]": "kwby1", "query[1][value]": "summary",\
            "query[2][name]":"search","query[2][value]":{keyword}, "query[3][name]":"date1","query[3][value]":{start},"query[4][name]": "date2","query[4][value]": {end},\
            "query[5][name]": "feed_id","query[5][value]": "1","query[6][name]": "submit","query[6][value]": "next"}
            req_next = requests.post("https://promedmail.org/wp-admin/admin-ajax.php",headers=headers,data=params_next)
            # cnt_next=req_next.json()['res_count']
            results_next=req_next.json()['results']
            results = results + results_next
            i=i+1
        id_list=get_id(results,keyword)
        return id_list
    #50을 넘지 않으면 바로 전체 수를 가지고 와라
    else:
        id_list=get_id(results,keyword)
        return id_list

#만들어진 링크 리스트에서 각 링크 들고와서 각 화면의 글 가져오기
def get_content(headers,id_list):
    content = []
    for key_id in id_list:
        params_link={'action':'get_latest_post_data','alertId':{key_id[1]}}
        req_link = requests.post("https://promedmail.org/wp-admin/admin-ajax.php",headers=headers,data=params_link)
        link_text = bs(req_link.text,'html.parser')
        headline = link_text.div.find_all(string=True)[0]
        date = link_text.find('span',{'class':'\\"blue\\"'}).get_text()[24:34]
        body = link_text.div.find_all(string=True)[7:]
        content.append((key_id[0],key_id[1],headline,date,body))
    
    return content

def buildup(result):
    df=pd.DataFrame(result)
    df=df.rename(columns={0:'keyword',1:'id',2:'headline',3:'date',4:'body'})

    # df['body'] = df['body'].apply(lambda x:re.sub(r"[,'\[\]\\\\]",'',str(x)))
    # df['headline']=df['headline'].str.lower()
    # df['body']=df['body'].str.lower()
    # df['body']=df['body'].apply(lambda x : re.sub(r'\S*@\S*\s?','',str(x)))
    df['body']=df['body'].str.rsplit('see also',1,expand=True)[0]

    return df

def search_data(list_name,start,end):
    headers = {"referer" : "https://promedmail.org/promed-posts/", 
          "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36"}
    # start = '07/01/2020'
    # end = datetime.datetime.strftime(datetime.date.today(),'%m/%d/%Y')
    promed_news=[]
    for keyword in tqdm(list_name):
        id_list = get_All_link_proMED(headers,start,end,keyword)
        content=get_content(headers,id_list)
        promed_news += content

    result=buildup(promed_news)

    return result


#수집기로 DB에 넣거나 csv파일로 떨굴 시에 사용할 코드

# discovered=pd.read_excel("./search_keyword.xlsx",sheet_name="discovered")
# undiscovered =pd.read_excel("./search_keyword.xlsx",sheet_name="undiscovered")

# discovered=discovered.DISCOVERED_DISEASE.tolist()
# undiscovered=undiscovered.UNDISCOVERED_DISEASE.tolist()

# start='07/01/2020'
# end=datetime.datetime.strftime(datetime.date.today(),'%m/%d/%Y')

# results1=search_data(discovered,start,end)
# results2 = search_data(undiscovered,start,end)

## 행 단위로 붙인 하나의 dataframe으로 만들기 / 그게 아니면 따로 넣어두기
#df = pd.concat([result1,result2],axis=0)

# ##DB
# import pymysql
# from sqlalchemy import create_engine
# import mysql.connector

# #DB config
# HOST = host name
# PORT = port
# USER = user id
# PASSWD = password
# DB = db name

# #DB connection
# engine=create_engine("mysql+mysqlconnector://"+USER+":"+PASSWD+"@"+HOST+"/"+DB, echo=False)

# df.to_sql(name=table, con=engine,if_exists='append',index=False)

# #CSV
# results1.to_csv('./discovered.csv',index=False)
# results2.to_csv("./undiscovered.csv",index=False)
