from __future__ import annotations
import os, urllib.parse
from .core import Result, SC_BASE, dedupe, get_json, trim, web_index, window

def _sc_headers(token:str)->dict[str,str]:return {"x-api-key":token,"Accept":"application/json"}
def _search_linkedin_public(query:str,days:int,limit:int)->list[Result]:
    start,_,_=window(days);lanes=[(f"site:linkedin.com/pulse {query} after:{start}",.95,"article"),(f"site:linkedin.com/posts {query} after:{start}",.84,"post"),(f"site:linkedin.com/in {query}",.62,"profile_index_entry")];out=[]
    for lane,boost,kind in lanes:
        try:
            for hit in web_index(lane,max(4,limit//2),"linkedin"):
                hit.score=min(.99,(hit.score+boost)/2);hit.metadata.update({"content_type":kind,"authenticated_linkedin_access":False,"live_role_validation":False,"canonical_identity_resolution":False});out.append(hit)
        except Exception:pass
    return dedupe(out,limit)
def _search_linkedin_sc(query:str,days:int,limit:int,token:str)->list[Result]:
    posted="last-week" if days<=7 else "last-month";data=get_json(f"{SC_BASE}/linkedin/search/posts?"+urllib.parse.urlencode({"query":query,"date_posted":posted}),headers=_sc_headers(token),retries=1);rows=(data.get("posts") or data.get("results") or data.get("data") or []) if isinstance(data,dict) else [];out=[]
    for row in rows[:limit]:
        if not isinstance(row,dict):continue
        url=row.get("url") or row.get("postUrl") or row.get("linkedinUrl") or ""
        if not url:continue
        title=trim(row.get("title") or row.get("text") or row.get("content") or "LinkedIn post",350);out.append(Result("linkedin",title,url,trim(row.get("text") or row.get("content")),str(row.get("date") or row.get("postedAt") or "")[:10] or None,trim(row.get("author") or row.get("authorName"),200) or None,.82,{"acquisition_method":"scrapecreators_optional","commercial_provider":True,"live_role_validation":False}))
    return out
def search_linkedin(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    public=_search_linkedin_public(query,days,limit);token=os.getenv("SCRAPECREATORS_API_KEY","").strip();paid=[]
    if allow_commercial and token:
        try:paid=_search_linkedin_sc(query,days,limit,token)
        except Exception:pass
    return dedupe([*paid,*public],limit)
