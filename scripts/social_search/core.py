from __future__ import annotations
import datetime as dt, html, json, re, time, urllib.error, urllib.parse, urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Iterable

VERSION="0.2.0"; UA=f"search-social-networks/{VERSION}"; SC_BASE="https://api.scrapecreators.com/v1"
@dataclass
class Result:
    source:str; title:str; url:str; snippet:str=""; date:str|None=None; author:str|None=None; score:float=.5; metadata:dict[str,Any]=field(default_factory=dict)
    def key(self)->str:return canonical_url(self.url)
@dataclass
class SourceRun:
    source:str; status:str; results:list[Result]; error:str|None=None; elapsed_ms:int=0

def canonical_url(url:str)->str:
    if not url:return ""
    p=urllib.parse.urlsplit(url.strip()); noise={"utm_source","utm_medium","utm_campaign","utm_term","utm_content","ref","ref_src","source","feature","si"}
    q=[(k,v) for k,v in urllib.parse.parse_qsl(p.query,keep_blank_values=True) if k.lower() not in noise]
    return urllib.parse.urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/") or "/",urllib.parse.urlencode(q),""))

def http(url:str,*,method:str="GET",data:dict[str,Any]|None=None,headers:dict[str,str]|None=None,timeout:int=25,retries:int=2)->bytes:
    h={"User-Agent":UA,"Accept":"*/*"}; h.update(headers or {}); body=None if data is None else json.dumps(data).encode()
    if body is not None:h.setdefault("Content-Type","application/json")
    for attempt in range(retries+1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=h,method=method),timeout=timeout) as r:return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in {408,425,429,500,502,503,504} or attempt==retries:raise
        except (urllib.error.URLError,TimeoutError,OSError):
            if attempt==retries:raise
        time.sleep(min(3,.5*2**attempt))
    return b""

def get_json(url:str,**kwargs:Any)->Any:return json.loads(http(url,**kwargs).decode("utf-8","replace"))
def window(days:int)->tuple[str,str,int]:
    end=dt.datetime.now(dt.timezone.utc).date(); start=end-dt.timedelta(days=max(1,days)); epoch=int(dt.datetime.combine(start,dt.time.min,tzinfo=dt.timezone.utc).timestamp()); return start.isoformat(),end.isoformat(),epoch

def trim(v:Any,n:int=1200)->str:return re.sub(r"\s+"," ",str(v or "")).strip()[:n]
def tokens(text:str)->set[str]:
    stop={"the","and","for","with","from","this","that","how","what","les","des","une","dans","pour","avec","sur","qui","que"}; return {x for x in re.findall(r"[a-z0-9][a-z0-9_+.-]{1,}",text.lower()) if x not in stop}
def relevance(query:str,text:str)->float:
    q=tokens(query); return .5 if not q else min(1,.25+.75*len(q&tokens(text))/len(q))
def merge_meta(dst:dict[str,Any],src:dict[str,Any])->None:
    for k,v in src.items():
        if k not in dst or not dst[k]:dst[k]=v
def dedupe(items:Iterable[Result],limit:int)->list[Result]:
    best:{}={}
    for item in items:
        key=item.key()
        if not key:continue
        old=best.get(key)
        if old is None:best[key]=item
        elif item.score>old.score:merge_meta(item.metadata,old.metadata); best[key]=item
        else:merge_meta(old.metadata,item.metadata)
    return sorted(best.values(),key=lambda x:(x.score,x.date or ""),reverse=True)[:limit]

class DDGParser(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.mode="";self.buf=[];self.current=None
    def handle_starttag(self,tag,attrs):
        data=dict(attrs);cls=data.get("class") or ""
        if tag=="a" and "result__a" in cls:self.mode="title";self.buf=[];self.current={"url":data.get("href") or "","title":"","snippet":""}
        elif tag in {"a","div"} and "result__snippet" in cls and self.rows:self.mode="snippet";self.buf=[]
    def handle_endtag(self,tag):
        if tag=="a" and self.mode=="title" and self.current:self.current["title"]=" ".join(self.buf).strip();self.rows.append(self.current);self.mode=""
        elif tag in {"a","div"} and self.mode=="snippet":self.rows[-1]["snippet"]=" ".join(self.buf).strip();self.mode=""
    def handle_data(self,data):
        if self.mode:self.buf.append(data)
def unwrap_ddg(url:str)->str:
    if url.startswith("//"):url="https:"+url
    p=urllib.parse.urlparse(url);target=urllib.parse.parse_qs(p.query).get("uddg");return urllib.parse.unquote(target[0]) if target else url
def web_index(query:str,limit:int=10,source:str="web")->list[Result]:
    raw=http("https://html.duckduckgo.com/html/?"+urllib.parse.urlencode({"q":query}),headers={"Accept":"text/html"}).decode("utf-8","replace");parser=DDGParser();parser.feed(raw);out=[]
    for i,row in enumerate(parser.rows[:max(15,limit*3)]):
        url=unwrap_ddg(row.get("url",""))
        if not url.startswith("http"):continue
        title=html.unescape(trim(row.get("title"),500));snippet=html.unescape(trim(row.get("snippet"),1400));out.append(Result(source,title,url,snippet,score=min(.95,.45+.45*relevance(query,f"{title} {snippet}")-i*.01),metadata={"acquisition_method":"public_web_index"}))
    return dedupe(out,limit)
def search_web(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    start,end,_=window(days);out=web_index(f"{query} after:{start} before:{end}",limit,"web")
    for r in out:r.metadata.update({"window_start":start,"window_end":end})
    return out
