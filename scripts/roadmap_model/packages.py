# SPDX-License-Identifier: MIT
"""Package evidence record for the architecture page (audit of 10 Nov 2026).

Facts git knows are generated here. The committed record is a snapshot of the repositories at generation time:
check_roadmap.py compares the page with that record, and `--check` (run daily by .github/workflows/package-drift.yml)
compares the record with the repositories, so a newer upstream commit shows up as drift until the record is regenerated. That covers the package list, repository, path,
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
import hashlib
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
    """rc.1 pin of one package. Compares the package tree, not the repository commit: an equal tree means the package
    content matches main even when the pinned commit differs; a different tree only means it differs (no ancestry
    claim)."""
    if not pin:
        return {"sha": None, "present": False, "same_as_main": False, "label": "not pinned"}
    t = tree(d, pin, path)
    same = t is not None and t == tree(d, main_sha, path)
    label = "not in the pin" if t is None else ("package content matches main" if same else "differs from main")
    return {"sha": pin, "present": t is not None, "same_as_main": same, "label": label}


def parse_package(text):
    """name, description, licences and dependency names of one package.xml."""
    root = ET.fromstring(text)
    desc = re.sub(r"\s+", " ", (root.findtext("description") or "")).strip()
    desc = re.sub(r"\s*\u2014\s*", ", ", desc)   # no em dash on public pages
    deps = sorted({(e.text or "").strip() for t in DEP_TAGS for e in root.findall(t) if (e.text or "").strip()})
    return {"name": (root.findtext("name") or "").strip(), "description": desc,
            "license": [(e.text or "").strip() for e in root.findall("license")], "deps": deps}


def evidence_ok(status, ev):
    """A "tested" badge names its check, run link, tested commit and profile, the run concluded "success", and the package
    tree at the tested commit equals the displayed head (`applies`). check_roadmap.py applies the same rule."""
    if status != "MERGED AND TESTED":
        return True
    return bool(ev and ev.get("check") and str(ev.get("run", "")).startswith("https://") and ev.get("commit")
                and ev.get("profile") and ev.get("conclusion") == "success" and ev.get("applies") is True)


def evidence_applies(d, ev, main_sha, path):
    """True when the package tree at the tested commit equals the tree at the displayed head of main."""
    if not ev.get("commit"):
        return None
    try:
        full = git(d, "rev-parse", ev["commit"]).strip()
    except subprocess.CalledProcessError:
        return False
    return tree(d, full, path) is not None and tree(d, full, path) == tree(d, main_sha, path)


def build(clones, rc1_file, date):
    dirs = {r: clone(clones, r) for r in REPOS}
    heads = {r: head(dirs[r]) for r in REPOS}
    if rc1_file:
        text = open(rc1_file, encoding="utf-8").read()
        rc1_source = {"repo": None, "commit": None, "path": rc1_file}
    else:
        text = git(dirs["openamrobot-manifest"], "show", "origin/HEAD:releases/v2.0.0-rc.1.repos")
        rc1_source = {"repo": "openamrobot-manifest", "commit": heads["openamrobot-manifest"]["sha"],
                      "path": "releases/v2.0.0-rc.1.repos"}
    rc1_source["sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    pins = {v["url"].rstrip("/").split("/")[-1].removesuffix(".git"): v["version"]
            for v in yaml.safe_load(text)["repositories"].values()}
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
        ev = dict(st.get("evidence") or {})
        if ev:
            ev["applies"] = evidence_applies(dirs[r], ev, sha, os.path.dirname(prov["path"]))
        if not evidence_ok(st["status"], ev):
            errors.append("%s: MERGED AND TESTED needs check, run, commit, profile, conclusion success and a tested "
                          "package tree equal to the displayed head" % name)
        packages[name] = {
            "name": name, "repo": r, "path": prov["path"], "description": prov["description"], "license": prov["license"],
            "url": "%s%s/blob/%s/%s" % (ORG, r, sha, prov["path"]),
            "deps_internal": sorted(d for d in prov["deps"] if d in names and d != name),
            "deps_external": sorted(d for d in prov["deps"] if d not in names),
            "main": {"sha": sha, "date": heads[r]["date"]},
            "rc1": rc1_state(dirs[r], sha, pin, os.path.dirname(prov["path"])),
            "duplicates": ["%s/%s" % (p["repo"], p["path"]) for p in provs if p is not prov],
            "status": st["status"], "evidence": ev, "prs": st.get("prs", []),
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


def drift(old, new):
    """What changed upstream since the committed record: heads of main, rc.1 pins, the package list."""
    out = []
    for r, h in new["heads"].items():
        o = old.get("heads", {}).get(r, {}).get("sha")
        if o != h["sha"]:
            out.append("%s main %s -> %s" % (r, (o or "none")[:7], h["sha"][:7]))
    for r, sha in new["rc1_pins"].items():
        if old.get("rc1_pins", {}).get(r) != sha:
            out.append("rc.1 pin %s %s -> %s" % (r, (old.get("rc1_pins", {}).get(r) or "none")[:7], sha[:7]))
    for n in sorted(set(new["packages"]) ^ set(old.get("packages", {}))):
        out.append("package %s %s" % (n, "added" if n in new["packages"] else "removed"))
    return out


def script_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def rc1_word(r):
    return r["label"] + (" (%s)" % r["sha"][:7] if r["sha"] and not r["same_as_main"] else "")


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
    ap.add_argument("--check", action="store_true",
                    help="compare the committed record with the repositories now; exit 1 on drift, write nothing")
    a = ap.parse_args()
    os.makedirs(a.clones, exist_ok=True)
    rec = build(a.clones, a.rc1, a.date)
    if a.check:
        diffs = drift(json.load(open(OUT, encoding="utf-8")), rec)
        for d in diffs:
            print("drift:", d)
        print("packages.json is current" if not diffs else "packages.json is behind the repositories: rerun packages.py")
        raise SystemExit(1 if diffs else 0)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1, ensure_ascii=False)
        f.write("\n")
    write_page(rec)
    src = rec["rc1_source"]
    print("packages.json: %d packages, %d other; rc.1 from %s %s %s" % (len(rec["packages"]), len(rec["other"]),
          src.get("repo"), (src.get("commit") or "")[:7], src["path"]))


if __name__ == "__main__":
    main()
