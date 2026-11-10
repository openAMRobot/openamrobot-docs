# SPDX-License-Identifier: MIT
"""Package evidence record for the architecture page (audit of 10 Nov 2026).

Facts git knows are generated here, so they can not drift. That covers the package list, repository, path,
package.xml description, licence, dependencies, the head of main, the v2.0.0-rc.1 pin and whether the package exists
in that pin, and duplicate providers. What a person must judge stays in `package_status.yaml`: the badge, the named
check, its run, the tested commit and profile, and the open PRs. Firmware and placeholder entries come from
`firmware.yaml`.

Outputs:
  docs/assets/roadmap/model/packages.json   the record (heads, rc.1 pins, packages, other), read by check_roadmap.py
  docs/assets/roadmap/architecture.html     `var PK` (package cards), `var FW` (firmware and placeholders), the
                                            box status classes, the "Three layers" count strip and the FW list

Usage (needs network; CI reads only the committed outputs):
  python3 scripts/roadmap_model/packages.py [--clones DIR] [--rc1 FILE] [--date YYYY-MM-DD]
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PAGE = os.path.join(ROOT, "docs", "assets", "roadmap", "architecture.html")
OUT = os.path.join(ROOT, "docs", "assets", "roadmap", "model", "packages.json")
ORG = "https://github.com/openAMRobot/"
REPOS = ["openamr-platform-sw", "openamr-upperbody-sw", "openamrobot-interfaces", "openamrobot-ui",
         "openamrobot-manipulation", "openamr-platform-fw", "openamr-upperbody-fw", "openamrobot-manifest"]
SCAN = REPOS[:5]   # repositories whose ROS packages are drawn as cards
CLASS = {"MERGED AND TESTED": "st-mat", "MERGED UNTESTED": "st-mun", "IN REVIEW": "st-rev"}
DEP_TAGS = ("depend", "build_depend", "exec_depend", "buildtool_depend", "test_depend", "build_export_depend")

sys.path.insert(0, HERE)
from bom714 import obj_span  # noqa: E402


def git(repo_dir, *args):
    return subprocess.run(["git", "-C", repo_dir] + list(args), check=True, capture_output=True, text=True).stdout


def clone(clones, repo):
    d = os.path.join(clones, repo)
    if not os.path.isdir(os.path.join(d, ".git")):
        subprocess.run(["git", "clone", "-q", ORG + repo, d], check=True)
    git(d, "fetch", "-q", "origin")
    return d


def head(d):
    sha = git(d, "rev-parse", "origin/HEAD").strip()
    return {"sha": sha, "date": git(d, "show", "-s", "--format=%cs", sha).strip()}


def has(d, sha, path):
    return subprocess.run(["git", "-C", d, "cat-file", "-e", "%s:%s" % (sha, path)], capture_output=True).returncode == 0


def tree(d, sha, path):
    """Object id of a path at a commit, or None."""
    r = subprocess.run(["git", "-C", d, "rev-parse", "%s:%s" % (sha, path)], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def rc1_state(d, main_sha, pin, path):
    """rc.1 pin of one package: present, and equal to main or older."""
    if not pin:
        return {"sha": None, "present": False, "same_as_main": False}
    t = tree(d, pin, path)
    return {"sha": pin, "present": t is not None, "same_as_main": t is not None and t == tree(d, main_sha, path)}


def parse_package(text):
    """name, description, licences and dependency names of one package.xml."""
    root = ET.fromstring(text)
    desc = re.sub(r"\s+", " ", (root.findtext("description") or "")).strip()
    desc = re.sub(r"\s*\u2014\s*", ", ", desc)   # no em dash on public pages
    deps = sorted({(e.text or "").strip() for t in DEP_TAGS for e in root.findall(t) if (e.text or "").strip()})
    return {"name": (root.findtext("name") or "").strip(), "description": desc,
            "license": [(e.text or "").strip() for e in root.findall("license")], "deps": deps}


def rc1_pins(path):
    data = yaml.safe_load(open(path, encoding="utf-8"))["repositories"]
    return {v["url"].rstrip("/").split("/")[-1].removesuffix(".git"): v["version"] for v in data.values()}


def evidence_ok(status, ev):
    """A "tested" badge names its check, run link, tested commit and profile (check_roadmap.py applies the same rule)."""
    if status != "MERGED AND TESTED":
        return True
    return bool(ev and ev.get("check") and str(ev.get("run", "")).startswith("https://") and ev.get("commit")
                and ev.get("profile"))


def build(clones, rc1_file, date):
    dirs = {r: clone(clones, r) for r in REPOS}
    heads = {r: head(dirs[r]) for r in REPOS}
    if rc1_file:
        pins, rc1_source = rc1_pins(rc1_file), rc1_file
    else:
        text = git(dirs["openamrobot-manifest"], "show", "origin/HEAD:releases/v2.0.0-rc.1.repos")
        pins = {v["url"].rstrip("/").split("/")[-1].removesuffix(".git"): v["version"]
                for v in yaml.safe_load(text)["repositories"].values()}
        rc1_source = "openamrobot-manifest main %s" % heads["openamrobot-manifest"]["sha"][:7]
    status = yaml.safe_load(open(os.path.join(HERE, "package_status.yaml"), encoding="utf-8"))
    found = {}
    for r in SCAN:
        sha = heads[r]["sha"]
        for path in git(dirs[r], "ls-tree", "-r", "--name-only", sha).split():
            if path.endswith("package.xml"):
                p = parse_package(git(dirs[r], "show", "%s:%s" % (sha, path)))
                found.setdefault(p["name"], []).append(dict(p, repo=r, path=path))
    packages, errors = {}, []
    names = set(found)
    for name, provs in sorted(found.items()):
        st = status["packages"].get(name)
        if st is None:
            errors.append("%s: no entry in package_status.yaml" % name)
            continue
        prov = next((p for p in provs if p["repo"] == st.get("provider", provs[0]["repo"])), provs[0])
        r, sha = prov["repo"], heads[prov["repo"]]["sha"]
        pin = pins.get(r)
        if not evidence_ok(st["status"], st.get("evidence")):
            errors.append("%s: MERGED AND TESTED needs evidence check, run, commit and profile" % name)
        packages[name] = {
            "name": name, "repo": r, "path": prov["path"], "description": prov["description"], "license": prov["license"],
            "url": "%s%s/blob/%s/%s" % (ORG, r, sha, prov["path"]),
            "deps_internal": sorted(d for d in prov["deps"] if d in names and d != name),
            "deps_external": sorted(d for d in prov["deps"] if d not in names),
            "main": {"sha": sha, "date": heads[r]["date"]},
            "rc1": rc1_state(dirs[r], sha, pin, os.path.dirname(prov["path"])),
            "duplicates": ["%s/%s" % (p["repo"], p["path"]) for p in provs if p is not prov],
            "status": st["status"], "evidence": st.get("evidence") or {}, "prs": st.get("prs", []),
            "note": st.get("note", ""), "area": st["area"],
        }
    for name in status["packages"]:
        if name not in found:
            errors.append("%s: in package_status.yaml but no package.xml on main" % name)
    other = []
    for e in yaml.safe_load(open(os.path.join(HERE, "firmware.yaml"), encoding="utf-8"))["entries"]:
        r = e["repo"]
        sha = heads[r]["sha"]
        pin = pins.get(r)
        if not has(dirs[r], sha, e["path"]):
            errors.append("%s: %s not on %s main" % (e["name"], e["path"], r))
        other.append(dict(e, url="%s%s/tree/%s/%s" % (ORG, r, sha, e["path"]), main={"sha": sha, "date": heads[r]["date"]},
                          rc1=rc1_state(dirs[r], sha, pin, e["path"])))
    if errors:
        raise SystemExit("packages.py: " + "; ".join(errors))
    return {"generated": date, "rc1_source": rc1_source, "heads": heads, "rc1_pins": pins, "packages": packages,
            "other": other}


def script_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def rc1_word(r):
    return "same as main" if r["same_as_main"] else ("older than main (%s)" % r["sha"][:7] if r["present"] else "no")


FW_START, FW_END = "<!-- packages:other -->", "<!-- /packages:other -->"


def other_html(rec):
    rows = []
    for e in rec["other"]:
        rows.append('<tr><td><a href="%s" target="_blank" rel="noopener">%s</a></td><td>%s</td><td>%s</td><td>%s</td>'
                    '<td>%s</td></tr>' % (e["url"], e["name"], e["repo"], e["state"],
                                          rc1_word(e["rc1"]), e["evidence"]))
    return (FW_START + '<h3>Firmware and placeholders (not drawn above)</h3><table class="small"><thead><tr><th>Entry</th>'
            '<th>Repository</th><th>State</th><th>In rc.1 pin</th><th>Evidence</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table>" + FW_END)


def write_page(rec, page=PAGE):
    s = open(page, encoding="utf-8").read()
    a, b = obj_span(s, "var PK")
    old = json.loads(s[a:b])
    pk = {}
    for name, p in rec["packages"].items():
        keep = old.get(name, {})
        pk[name] = dict(p, nodes=keep.get("nodes", []), topics=keep.get("topics", []), findings=keep.get("findings", []))
    pk = {n: pk[n] for n in list(old) + [n for n in pk if n not in old] if n in pk}
    s = s[:a] + script_json(pk) + s[b:]
    if "var FW" in s:
        a, b = obj_span(s, "var FW")
        s = s[:a] + script_json(rec["other"]) + s[b:]
    else:
        s = s.replace("var PK=", "var FW=%s;\nvar PK=" % script_json(rec["other"]), 1)
    for name, p in pk.items():
        cls = CLASS[p["status"]]
        s = re.sub(r'<g class="pk st-[a-z]+" data-st="st-[a-z]+" data-p="%s" tabindex="0" role="button" aria-label="%s, [A-Z ]+"'
                   % (re.escape(name), re.escape(name)),
                   '<g class="pk %s" data-st="%s" data-p="%s" tabindex="0" role="button" aria-label="%s, %s"'
                   % (cls, cls, name, name, p["status"]), s)
    boxes = re.findall(r'data-st="(st-[a-z]+)" data-p="', s)   # a package drawn in two repositories counts twice
    n = {c: boxes.count(c) for c in ("st-mat", "st-mun")}
    s = re.sub(r'(data-hl="st-mat"[^>]*>.*?<b class="num">)\d+(</b> merged and tested)', r"\g<1>%d\2" % n["st-mat"], s, count=1,
               flags=re.S)
    s = re.sub(r'(data-hl="st-mun"[^>]*>.*?<b class="num">)\d+(</b> merged untested)', r"\g<1>%d\2" % n["st-mun"], s, count=1,
               flags=re.S)
    block = other_html(rec)
    if FW_START in s:
        s = s[:s.index(FW_START)] + block + s[s.index(FW_END) + len(FW_END):]
    else:
        i = s.index("</section>", s.index('<section class="card" id="layers">'))
        s = s[:i] + block + s[i:]
    open(page, "w", encoding="utf-8").write(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clones", default="/tmp/oamr_package_clones")
    ap.add_argument("--rc1", default=None, help="rc.1 .repos file; default: releases/v2.0.0-rc.1.repos on manifest main")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args()
    os.makedirs(a.clones, exist_ok=True)
    rec = build(a.clones, a.rc1, a.date)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1, ensure_ascii=False)
        f.write("\n")
    write_page(rec)
    print("packages.json: %d packages, %d other; rc.1 from %s" % (len(rec["packages"]), len(rec["other"]), rec["rc1_source"]))


if __name__ == "__main__":
    main()
