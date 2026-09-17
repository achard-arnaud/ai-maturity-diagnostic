from __future__ import annotations
import html,os,re,urllib.parse,xml.etree.ElementTree as ET
from typing import Any
from .core import Result,dedupe,get_json,http,trim,web_index,window

def search_hackernews(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    _,_,epoch=window(days);params=urllib.parse.urlencode({"query":query,"tags":"story","numericFilters":f"created_at_i>{epoch}","hitsPerPage":min(50,max(10,limit*2))});data=get_json("https://hn.algolia.com/api/v1/search_by_date?"+params);out=[]
    for row in data.get("hits",[]):
        oid=row.get("objectID");url=row.get("url") or (f"https://news.ycombinator.com/item?id={oid}" if oid else "")
        if not url:continue
        points,comments=int(row.get("points") or 0),int(row.get("num_comments") or 0);meta={"points":points,"comments":comments,"discussion_url":f"https://news.ycombinator.com/item?id={oid}" if oid else None,"acquisition_method":"hn_algolia_public_api"}
        if enrich and oid:
            try:
                item=get_json(f"https://hn.algolia.com/api/v1/items/{oid}");meta["top_comments"]=[{"author":c.get("author"),"text":trim(re.sub(r"<[^>]+>"," ",c.get("text") or ""),700),"points":c.get("points")} for c in (item.get("children") or [])[:5] if isinstance(c,dict)]
            except Exception:pass
        out.append(Result("hackernews",row.get("title") or "Hacker News",url,"",(row.get("created_at") or "")[:10],row.get("author"),min(.99,.52+min(.25,points/800)+min(.12,comments/500)),meta))
    return dedupe(out,limit)

def github_token()->str:return (os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or "").strip()
def github_headers()->dict[str,str]:
    h={"Accept":"application/vnd.github+json"};token=github_token()
    if token:h["Authorization"]=f"Bearer {token}"
    return h
def search_github(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    start,_,_=window(days);out=[]
    for kind,endpoint,base in (("repository","repositories",.75),("issue","issues",.68)):
        params=urllib.parse.urlencode({"q":f"{query} updated:>={start}","sort":"updated","order":"desc","per_page":min(50,limit)})
        try:data=get_json(f"https://api.github.com/search/{endpoint}?{params}",headers=github_headers())
        except Exception:continue
        for row in data.get("items",[]):
            if kind=="repository":
                meta={"kind":kind,"stars":row.get("stargazers_count"),"forks":row.get("forks_count"),"language":row.get("language"),"acquisition_method":"github_public_rest"};out.append(Result("github",row.get("full_name") or row.get("name") or "GitHub repository",row.get("html_url") or "",trim(row.get("description")),(row.get("updated_at") or "")[:10],(row.get("owner") or {}).get("login"),min(.98,base+min(.12,int(row.get("stargazers_count") or 0)/100000)),meta))
            else:
                meta={"kind":"pull_request" if row.get("pull_request") else "issue","state":row.get("state"),"comments":row.get("comments"),"acquisition_method":"github_public_rest"}
                if enrich and row.get("comments_url"):
                    try:
                        cs=get_json(row["comments_url"],headers=github_headers());meta["top_comments"]=[{"author":(c.get("user") or {}).get("login"),"text":trim(c.get("body"),700)} for c in cs[:5] if isinstance(c,dict)]
                    except Exception:pass
                out.append(Result("github",row.get("title") or "GitHub issue/PR",row.get("html_url") or "",trim(row.get("body")),(row.get("updated_at") or "")[:10],(row.get("user") or {}).get("login"),base,meta))
    return dedupe((x for x in out if x.url),limit)

def _reddit_ref(url:str)->tuple[str,str]|None:
    m=re.search(r"reddit\.com/r/([^/]+)/comments/([^/]+)",url);return (m.group(1),m.group(2)) if m else None
def _reddit_comments(url:str,limit:int=5)->list[dict[str,Any]]:
    ref=_reddit_ref(url)
    if not ref:return []
    sub,post=ref
    for endpoint in (f"https://www.reddit.com/r/{sub}/comments/{post}.json?limit={limit}&sort=top",f"https://www.reddit.com/comments/{post}.json?limit={limit}&sort=top"):
        try:
            data=get_json(endpoint,headers={"Accept":"application/json"},retries=1)
            if isinstance(data,list) and len(data)>1:
                rows=data[1].get("data",{}).get("children",[]);return [{"author":x.get("data",{}).get("author"),"text":trim(x.get("data",{}).get("body"),700),"score":x.get("data",{}).get("score")} for x in rows[:limit] if isinstance(x,dict)]
        except Exception:pass
    return []
def search_reddit(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    start,_,_=window(days);out=[]
    try:
        root=ET.fromstring(http("https://www.reddit.com/search.rss?"+urllib.parse.urlencode({"q":query,"sort":"new","t":"month"}),headers={"Accept":"application/atom+xml"}));ns={"a":"http://www.w3.org/2005/Atom"}
        for i,entry in enumerate(root.findall("a:entry",ns)):
            date=(entry.findtext("a:updated",default="",namespaces=ns) or "")[:10]
            if date and date<start:continue
            link=entry.find("a:link",ns);url=link.attrib.get("href","") if link is not None else "";title=trim(entry.findtext("a:title",default="",namespaces=ns),500);body=html.unescape(trim(re.sub(r"<[^>]+>"," ",entry.findtext("a:content",default="",namespaces=ns) or ""),1200));meta={"acquisition_method":"reddit_public_rss"}
            if enrich and url:
                comments=_reddit_comments(url)
                if comments:meta["top_comments"]=comments
            out.append(Result("reddit",title,url,body,date,None,max(.45,.78-i*.02),meta))
    except Exception:pass
    if not out:
        try:
            out=web_index(f"site:reddit.com {query} after:{start}",limit,"reddit")
            for r in out:r.metadata["acquisition_method"]="public_web_index_fallback"
        except Exception:return []
    return dedupe(out,limit)
