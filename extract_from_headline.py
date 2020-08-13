import pandas as pd
import re
from geopy.geocoders import Nominatim
host='nominatim.openstreetmap.org'
geolocater=Nominatim(domain=host, timeout=8, user_agent="ms.kim1")
from tqdm import tqdm

### Extract from title : where, why, what
#제목으로부터 어느 질병, 장소 추출, 이외로도 감염원(혹은 대상--> 내용으로) 추출 가능

def extract_from_front(df):
    temp1 = pd.DataFrame(columns={'id','when','where','what','other'})
    temp2 = pd.DataFrame(columns={'id','when','where','what','other'})

    update=df[df['headline'].str.match('update')]
    rest=df[~df['headline'].str.match('update')]

    if len(update)>0:
        temp1['id'] = update['id']
        temp1['what']=update['headline'].str.split(' ',n=1,expand=True)[0]
    else:
        pass

    temp2 = location_disease(rest,temp2)
    
    return temp1,temp2


def check_nomination(result):
    for x in tqdm(range(len(result))):
        if (geolocater.geocode(result['other'][x]) is None) or (result['other'][x] is None) or (result['other'][x]=='None') :
            result['other'][x] = ''
        else:
            continue

    # result['other']=result['other'].apply(lambda x:'' if (geolocater.geocode(x) is None) or (geolocater.geocode(x) == 'None'))
    
    result['where']=result['where']+result['other']
    result.drop(['other'],axis=1,inplace=True)

    result['latitude'] = result['where'].apply(lambda x:'' if(geolocater.geocode(x) is None)or (geolocater.geocode(x) == 'None') else geolocater.geocode(x).latitude)
    result['longitude'] = result['where'].apply(lambda x:'' if (geolocater.geocode(x) is None)or (geolocater.geocode(x) == 'None') else geolocater.geocode(x).longitude)

    return result


def extract_from_title(flag,df):
    temp1, temp2 = extract_from_front(df)
    print("extract phrase based on headline")

    if flag == "discovered":
        temp1['what'] = df['keyword']
        temp2['what'] = df['keyword']
    elif flag == "undiscovered":
        pass
    
    result=pd.concat([temp1,temp2],axis=0)
    
    results=check_nomination(result)
    print("check and extract address")

    return results

def location_disease(df,temp):
    headline=df['headline']

    temp['id']=df['id']
    title=headline.str.split(" - ",n=1,expand=True)

    # temp['what']=title[0].str.split(",",n=1,expand=True)[0]
    temp['why'] = title[0].str.split(",",n=1,expand=True)[1]
    temp['where']=title[1].str.split(":",n=1,expand=True)[0]
    temp['other']=title[1].str.split(":",n=1,expand=True)[1]

    temp['other'] = temp['other'].str.replace('request for information','') # 1. ohther 열에서 REQUEST FOR INFORMATION, 숫자, 특수문자 삭제하기
    temp['other'] = temp['other'].apply(lambda x:re.sub('[^a-zA-Z]',' ',str(x))) #remove special characters
    temp['other'] = temp['other'].apply(lambda x:re.sub(r'\s+', ' ',str(x))) #remove digits

    temp['where'] = temp['where'].apply(lambda x:re.sub('[^a-zA-Z]',' ',str(x))) #remove special characters
    temp['where'] = temp['where'].apply(lambda x:re.sub(r'\s+', ' ',str(x))) #remove digits

    return temp

