from __future__ import annotations
import datetime as dt,os,urllib.parse,xml.etree.ElementTree as ET
from .core import Result,dedupe,get_json,http,relevance,search_web,trim,web_index,window

def search_arxiv(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    start,_,_=window(days);url="https://export.arxiv.org/api/query?"+urllib.parse.urlencode({"search_query":f"all:{query}","start":0,"max_results":max(10,limit*2),"sortBy":"submittedDate","sortOrder":"descending"});root=ET.fromstring(http(url,headers={"Accept":"application/atom+xml"}));ns={"a":"http://www.w3.org/2005/Atom"};out=[]
    for entry in root.findall("a:entry",ns):
        date=(entry.findtext("a:published",default="",namespaces=ns) or "")[:10]
        if date and date<start:continue
        authors=[a.findtext("a:name",default="",namespaces=ns) for a in entry.findall("a:author",ns)];title=trim(entry.findtext("a:title",default="",namespaces=ns),500);snippet=trim(entry.findtext("a:summary",default="",namespaces=ns),1600);out.append(Result("arxiv",title,entry.findtext("a:id",default="",namespaces=ns),snippet,date,", ".join(x for x in authors if x)[:500],.55+.4*relevance(query,f"{title} {snippet}"),{"acquisition_method":"arxiv_public_atom"}))
    return dedupe(out,limit)
def search_x(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    start,_,_=window(days);out=[]
    for lane in (f"site:x.com {query} after:{start}",f"site:twitter.com {query} after:{start}"):
        try:out.extend(web_index(lane,max(4,limit//2),"x"))
        except Exception:pass
    for r in out:r.metadata.update({"acquisition_method":"public_web_index","authenticated_x_access":False})
    return dedupe(out,limit)
def search_perplexity(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    key=os.getenv("PERPLEXITY_API_KEY","").strip()
    if not key:
        out=search_web(query,days,limit,enrich,allow_commercial)
        for r in out:r.source="perplexity";r.metadata.update({"perplexity_api_used":False,"fallback":"public_web_index"})
        return out
    start,end,_=window(days);data=get_json("https://api.perplexity.ai/search",method="POST",data={"query":query,"max_results":min(20,limit),"search_after_date_filter":dt.datetime.strptime(start,"%Y-%m-%d").strftime("%m/%d/%Y"),"search_before_date_filter":dt.datetime.strptime(end,"%Y-%m-%d").strftime("%m/%d/%Y")},headers={"Authorization":f"Bearer {key}","Accept":"application/json"});out=[]
    for i,row in enumerate(data.get("results",[]) if isinstance(data,dict) else []):
        if not isinstance(row,dict) or not row.get("url"):continue
        title,snippet=row.get("title") or row["url"],row.get("snippet") or "";out.append(Result("perplexity",title,row["url"],snippet,row.get("date"),None,min(.98,.52+.42*relevance(query,f"{title} {snippet}")-i*.01),{"acquisition_method":"perplexity_first_party_search_api","perplexity_api_used":True}))
    return dedupe(out,limit)
