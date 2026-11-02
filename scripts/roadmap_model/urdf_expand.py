#!/usr/bin/env python3
"""Expand the combined robot model (openamr-upperbody-sw combined_robot.xacro) without a ROS install.

Convergence phase 1 (warn only). Sets up a minimal ament index under ../ament (next to the repository), with
share/<package> symlinks and share/ament_index/resource_index/packages/<package> markers for:
  openamrobot_description            openamr-platform-sw at the PLATFORM-PIN (src/openamr-platform-sw@<pin>, a worktree)
  openamrobot_upperbody_description  openamr-upperbody-sw main
  openarm_description                openarm_description at its pinned commit
and a small ament_index_python stand-in (python/ament_index_python) that resolves those markers, then runs xacro
with the default arguments (bp000, hp30, lift joint at 0 = L1000) and with base_plate:=bp050. L1175 and L1350 are
lift-joint positions, set by parity.py. Writes:
  docs/assets/roadmap/model/combined_robot.urdf        default arguments (bp000)
  docs/assets/roadmap/model/combined_robot_bp050.urdf  base_plate:=bp050
and the source commits into source_snapshot.json (key combined_model; build.py keeps it).
Usage: python3 scripts/roadmap_model/urdf_expand.py [--pin 131e500]
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

from frames import MODEL, REPO, SRC

AMENT = os.path.abspath(os.path.join(REPO, "..", "ament"))
SHIM = '''"""Minimal stand-in for ament_index_python (written by openamrobot-docs scripts/roadmap_model/urdf_expand.py)."""
import os


class PackageNotFoundError(KeyError):
    pass


def _prefixes():
    return [p for p in os.environ.get("AMENT_PREFIX_PATH", "").split(os.pathsep) if p]


def get_package_prefix(package_name):
    for p in _prefixes():
        if os.path.exists(os.path.join(p, "share", "ament_index", "resource_index", "packages", package_name)):
            return p
    raise PackageNotFoundError("package '%s' not found, searching: %s" % (package_name, _prefixes()))


def get_package_share_directory(package_name, print_warning=True):
    return os.path.join(get_package_prefix(package_name), "share", package_name)
'''


def git(path, *a):
    return subprocess.check_output(["git", "-C", path] + list(a), text=True).strip()


def setup(pin):
    pf = os.path.join(SRC, "openamr-platform-sw")
    wt = os.path.join(SRC, "openamr-platform-sw@" + pin)
    if not os.path.isdir(wt):
        subprocess.check_call(["git", "-C", pf, "worktree", "add", "-q", wt, pin])
    pkgs = {
        "openamrobot_description": os.path.join(wt, "ros2", "src", "openamrobot_description"),
        "openamrobot_upperbody_description": os.path.join(SRC, "openamr-upperbody-sw", "ros2", "src", "openamrobot_upperbody_description"),
        "openarm_description": os.path.join(SRC, "openarm_description"),
    }
    idx = os.path.join(AMENT, "share", "ament_index", "resource_index", "packages")
    os.makedirs(idx, exist_ok=True)
    for name, path in pkgs.items():
        link = os.path.join(AMENT, "share", name)
        if os.path.islink(link):
            os.remove(link)
        os.symlink(path, link)
        open(os.path.join(idx, name), "w").close()
    shim = os.path.join(AMENT, "python", "ament_index_python")
    os.makedirs(shim, exist_ok=True)
    open(os.path.join(shim, "__init__.py"), "w").write(SHIM)
    open(os.path.join(shim, "packages.py"), "w").write("from . import PackageNotFoundError, get_package_prefix, get_package_share_directory  # noqa: F401\n")
    srcs = {
        "openamrobot_description": {"repository": "openAMRobot/openamr-platform-sw", "commit": git(wt, "rev-parse", "HEAD"), "role": "PLATFORM-PIN"},
        "openamrobot_upperbody_description": {"repository": "openAMRobot/openamr-upperbody-sw", "commit": git(os.path.dirname(os.path.dirname(os.path.dirname(pkgs["openamrobot_upperbody_description"]))), "rev-parse", "HEAD"), "role": "main"},
        "openarm_description": {"repository": "enactic/openarm_description", "commit": git(pkgs["openarm_description"], "rev-parse", "HEAD"), "role": "upstream pin"},
    }
    return pkgs, srcs


def expand(args):
    env = dict(os.environ, AMENT_PREFIX_PATH=AMENT, PYTHONPATH=os.path.join(AMENT, "python") + os.pathsep + os.environ.get("PYTHONPATH", ""))
    x = os.path.join(AMENT, "share", "openamrobot_upperbody_description", "urdf", "combined_robot.xacro")
    r = subprocess.run([sys.executable, "-c", "import sys, xacro; sys.argv[0] = \"xacro\"; xacro.main()", x] + args, env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("xacro expansion failed (%s): %s" % (" ".join(args) or "default arguments", r.stderr.strip()))
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pin", default="131e500", help="PLATFORM-PIN commit of openamr-platform-sw")
    a = ap.parse_args()
    pkgs, srcs = setup(a.pin)
    out = {}
    for name, args in (("combined_robot.urdf", []), ("combined_robot_bp050.urdf", ["base_plate:=bp050"])):
        u = expand(args)
        open(os.path.join(MODEL, name), "w").write(u)
        out[name] = {"xacro_args": args or ["defaults: column dold_v4_350, base_plate bp000, head_pitch hp30, base_tilt bt10, arm_package openarm, hardware_profile mock"],
                     "sha256": hashlib.sha256(u.encode()).hexdigest()}
        print(name, len(u), "bytes")
    sp = os.path.join(MODEL, "source_snapshot.json")
    snap = json.load(open(sp)) if os.path.exists(sp) else {}
    snap["combined_model"] = {"xacro": "openamrobot_upperbody_description/urdf/combined_robot.xacro", "sources": srcs, "outputs": out,
                              "lift_joint": {"L1000": 0.0, "L1175": 0.175, "L1350": 0.350},
                              "how": "scripts/roadmap_model/urdf_expand.py (pip xacro, minimal ament index under ../ament)"}
    json.dump(snap, open(sp, "w"), indent=1)


if __name__ == "__main__":
    main()
