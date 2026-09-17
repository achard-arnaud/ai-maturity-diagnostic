from __future__ import annotations
import html,json,os,re,shutil,subprocess,tempfile,urllib.parse,xml.etree.ElementTree as ET
from .core import Result,SC_BASE,dedupe,get_json,http,relevance,trim,web_index,window
from .linkedin import _sc_headers

def _clean_vtt(text:str,max_words:int=1800)->str:
    rows=[];seen=set()
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith("WEBVTT") or "-->" in line or re.fullmatch(r"\d+",line):continue
        line=trim(html.unescape(re.sub(r"<[^>]+>","",line)),10000)
        if line and line not in seen:seen.add(line);rows.append(line)
    return " ".join(" ".join(rows).split()[:max_words])
def _youtube_transcript_ytdlp(url:str)->str:
    exe=shutil.which("yt-dlp")
    if not exe:return ""
    with tempfile.TemporaryDirectory(prefix="social-search-yt-") as tmp:
        cmd=[exe,url,"--skip-download","--write-subs","--write-auto-subs","--sub-langs","fr.*,en.*","--sub-format","vtt","-o",os.path.join(tmp,"%(id)s.%(ext)s"),"--quiet","--no-warnings"];subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45,check=False)
        for name in os.listdir(tmp):
            if name.endswith(".vtt"):
                with open(os.path.join(tmp,name),encoding="utf-8",errors="replace") as f:return _clean_vtt(f.read())
    return ""
def _youtube_transcript_direct(url:str)->str:
    vid=urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("v",[""])[0]
    if not vid:return ""
    try:
        page=http(f"https://www.youtube.com/watch?v={vid}",headers={"Accept":"text/html"},retries=1).decode("utf-8","replace");m=re.search(r'"captionTracks":(\[.*?\])[,}]',page)
        if not m:return ""
        tracks=json.loads(m.group(1));track=next((t for t in tracks if str(t.get("languageCode","")).startswith(("en","fr"))),tracks[0] if tracks else None)
        if not track or not track.get("baseUrl"):return ""
        xml=ET.fromstring(http(track["baseUrl"],retries=1));return " ".join("".join(x.itertext()) for x in xml.findall(".//text"))[:12000]
    except Exception:return ""
def _youtube_transcript_sc(url:str,token:str)->str:
    for ep in ("youtube/video-transcript","youtube/transcript"):
        try:
            data=get_json(f"{SC_BASE}/{ep}?"+urllib.parse.urlencode({"url":url}),headers=_sc_headers(token),retries=1);text=data.get("transcript") or data.get("text") or data.get("data") if isinstance(data,dict) else ""
            if isinstance(text,list):text=" ".join(trim(x.get("text") if isinstance(x,dict) else x,500) for x in text)
            if text:return trim(text,12000)
        except Exception:pass
    return ""
def _youtube_transcript(url:str,allow_commercial:bool)->tuple[str,str]:
    try:text=_youtube_transcript_ytdlp(url)
    except Exception:text=""
    if text:return text,"yt-dlp"
    text=_youtube_transcript_direct(url)
    if text:return text,"youtube_public_captions_http"
    token=os.getenv("SCRAPECREATORS_API_KEY","").strip()
    if allow_commercial and token:
        text=_youtube_transcript_sc(url,token)
        if text:return text,"scrapecreators_optional"
    return "",""
def _youtube_comments_ytdlp(url:str,limit:int=5)->list[dict]:
    exe=shutil.which("yt-dlp")
    if not exe:return []
    proc=subprocess.run([exe,url,"--skip-download","--write-comments","--dump-single-json","--extractor-args",f"youtube:max_comments={limit}","--quiet","--no-warnings"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60,check=False)
    try:data=json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:return []
    return [{"author":trim(x.get("author"),120),"text":trim(x.get("text"),600),"likes":x.get("like_count")} for x in (data.get("comments") or [])[:limit] if isinstance(x,dict)]
def search_youtube(query:str,days:int,limit:int,enrich:bool,allow_commercial:bool=False)->list[Result]:
    start,_,_=window(days);out=[];exe=shutil.which("yt-dlp")
    if exe:
        try:
            proc=subprocess.run([exe,f"ytsearch{limit}:{query}","--dump-json","--skip-download","--dateafter",start.replace("-",""),"--no-warnings"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120,check=False)
            for line in proc.stdout.splitlines():
                try:row=json.loads(line)
                except json.JSONDecodeError:continue
                vid=row.get("id");url=row.get("webpage_url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "")
                if not url:continue
                date=row.get("upload_date");date=f"{date[:4]}-{date[4:6]}-{date[6:]}" if isinstance(date,str) and len(date)==8 else date;out.append(Result("youtube",row.get("title") or "YouTube video",url,trim(row.get("description")),date,row.get("channel") or row.get("uploader"),min(.98,.55+.35*relevance(query,f"{row.get('title','')} {row.get('description','')}")+min(.08,(row.get("view_count") or 0)/1e7)),{"views":row.get("view_count"),"likes":row.get("like_count"),"duration":row.get("duration"),"acquisition_method":"yt-dlp"}))
        except Exception:out=[]
    if not out and allow_commercial and os.getenv("SCRAPECREATORS_API_KEY"):
        try:
            data=get_json(f"{SC_BASE}/youtube/search?"+urllib.parse.urlencode({"query":query}),headers=_sc_headers(os.environ["SCRAPECREATORS_API_KEY"]),retries=1);rows=(data.get("videos") or data.get("results") or data.get("data") or []) if isinstance(data,dict) else []
            for row in rows[:limit]:
                if isinstance(row,dict):
                    url=row.get("url") or row.get("videoUrl") or ""
                    if url:out.append(Result("youtube",trim(row.get("title") or "YouTube video",400),url,trim(row.get("description")),str(row.get("date") or "")[:10] or None,trim(row.get("channel") or row.get("author"),200) or None,.72,{"acquisition_method":"scrapecreators_optional","commercial_provider":True}))
        except Exception:pass
    if not out:
        try:out=web_index(f"site:youtube.com/watch {query} after:{start}",limit,"youtube")
        except Exception:return []
    if enrich:
        for hit in out[:min(3,len(out))]:
            text,method=_youtube_transcript(hit.url,allow_commercial)
            if text:hit.metadata.update({"transcript":text,"transcript_words":len(text.split()),"transcript_method":method});hit.score=min(.99,hit.score+.08)
            try:
                comments=_youtube_comments_ytdlp(hit.url)
                if comments:hit.metadata["top_comments"]=comments
            except Exception:pass
    return dedupe(out,limit)
