#!/usr/bin/env python3
"""Account-wide public-repository analyzer.

Read-only with respect to scanned repositories. Uses GitHub's public REST API,
so it can inspect every public repository owned by OWNER without a token.
It classifies textual source by explicit evidence; names are never proofs.
"""
import json, os, re, urllib.request, urllib.parse
OWNER=os.getenv("GITHUB_OWNER","letsgo0226")
API="https://api.github.com"
UA={"User-Agent":"account-public-repo-analyzer","Accept":"application/vnd.github+json"}
TEXT_EXT={".py",".sh",".md",".txt",".json",".yml",".yaml",".c",".h",".cpp",".js",".ts",".rs",".go",".java",".rb",".pl",".lua",".tex"}
MAX_BYTES=int(os.getenv("MAX_FILE_BYTES","250000"))

def get(url):
    r=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(r,timeout=30) as f:return json.load(f)

def repos():
    out=[]; page=1
    while True:
        a=get(f"{API}/users/{OWNER}/repos?type=owner&per_page=100&page={page}")
        if not a:break
        out += [r for r in a if not r.get("private")]
        page+=1
    return out

def tree(repo,branch):
    q=urllib.parse.quote(branch,safe="")
    return get(f"{API}/repos/{OWNER}/{repo}/git/trees/{q}?recursive=1").get("tree",[])

def text(repo,path):
    u=f"https://raw.githubusercontent.com/{OWNER}/{repo}/HEAD/{urllib.parse.quote(path)}"
    try:
        r=urllib.request.Request(u,headers={"User-Agent":UA["User-Agent"]})
        with urllib.request.urlopen(r,timeout=20) as f:return f.read(MAX_BYTES+1)[:MAX_BYTES].decode("utf-8","replace")
    except Exception:return ""

def classify(s):
    z=s.lower()
    return {
      "tm_explicit": bool(re.search(r"turing|transition|\bdelta\b|\u03b4|tape|state",z)),
      "zeta_declared": bool(re.search(r"riemann|zeta|\u03b6",z)),
      "zeta_numeric": bool(re.search(r"mpmath.*zeta|mp\.zeta|zetac|dirichlet|n\*\*\(-s\)",z,re.S)),
      "godel_declared": bool(re.search(r"g[oö]del|goedel|godel",z)),
      "self_reference": bool(re.search(r"quine|__file__|self[-_ ]?(?:code|source|refer)",z)),
      "omega_declared": bool(re.search(r"omega|\u03c9|colim|direct.limit|inverse.limit",z)),
      "empirical_hooks": bool(re.search(r"sensor|measurement|experiment|observ(?:e|ation)|dataset",z)),
      "formal_boundary": bool(re.search(r"omega_attained.{0,8}(?:false|0)|final.{0,8}(?:false|0)|open.{0,8}(?:true|1)",z,re.S)),
    }

def scan(r):
    name=r["name"]; files=[]; corpus=[]
    try:t=tree(name,r["default_branch"])
    except Exception as e:return {"repo":name,"error":str(e)}
    for x in t:
        if x.get("type")!="blob" or x.get("size",0)>MAX_BYTES:continue
        p=x["path"]; ext=os.path.splitext(p)[1].lower()
        if ext in TEXT_EXT or p.lower().startswith("readme"):
            s=text(name,p)
            if s: files.append(p); corpus.append(s)
    c=classify("\n".join(corpus))
    return {"repo":name,"url":r["html_url"],"default_branch":r["default_branch"],"files_scanned":len(files),"program_files":[p for p in files if os.path.splitext(p)[1].lower() in TEXT_EXT and not p.startswith(".github/")],"evidence":c,"semantics":{"exact_encoding":"unverified","consistency_proved":False,"program_equals_zeta":False,"omega_computed":False,"all_logical_worlds_enumerated":False},"note":"Lexical evidence is a classifier, not a mathematical or empirical proof."}

def main():
    rs=repos(); records=[scan(r) for r in rs]
    out={"schema":"ACCOUNT_REPOSITORY_REFLECTION_GRAPH/v1","owner":OWNER,"scope":"owned public repositories","repository_count":len(rs),"private_repositories_excluded":True,"records":records,"global":{"omega":"formal boundary only","omega_attained":False,"open":True,"final":False}}
    json.dump(out,open("account_public_repo_registry.json","w"),ensure_ascii=False,indent=2)
    print(json.dumps({"owner":OWNER,"repos":len(rs),"output":"account_public_repo_registry.json","omega_attained":False,"open":True,"final":False}))
if __name__=="__main__":main()
