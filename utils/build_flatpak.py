"""
novelWriter - Flatpak Build
===========================

This file is a part of novelWriter
Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""  # noqa

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request

from pathlib import Path

from utils.common import (
    ROOT_DIR,
    appdataXml,
    extractVersion,
    makeCheckSum,
    readFile,
    stripVersion,
    toUpload,
    writeFile,
)

PIP_GENERATOR_URL = (
    "https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator.py"
)
PYQT_BASEAPP_ID = "com.riverbankcomputing.PyQt.BaseApp"
ENCHANT_RELEASES_API = "https://api.github.com/repos/rrthomas/enchant/releases/latest"


def processEnchant(bldDir: Path) -> None:
    """Generate the enchant.json flatpak module for the latest enchant release."""
    print("Generate Enchant Module")
    print("=======================")
    print("")

    outFile = bldDir / "enchant.json"

    try:
        print(f"Checking: {ENCHANT_RELEASES_API}")
        with urllib.request.urlopen(ENCHANT_RELEASES_API) as response:
            release = json.loads(response.read())

        tag = release["tag_name"]
        version = tag.removeprefix("v")
        fileName = f"enchant-{version}.tar.gz"
        url = f"https://github.com/rrthomas/enchant/releases/download/{tag}/{fileName}"

        print(f"Downloading: {url}")
        tarFile = bldDir / fileName
        urllib.request.urlretrieve(url, tarFile)
        checksum = hashlib.sha256(tarFile.read_bytes()).hexdigest()
        tarFile.unlink()

        print(f"Version: {version}")
        print(f"SHA256: {checksum}")

        module = {
            "name": "enchant",
            "buildsystem": "autotools",
            "post-install": [
                "install -Dm644 -T COPYING.LIB ${FLATPAK_DEST}/share/licenses/${FLATPAK_ID}/enchant-COPYING.LIB",
            ],
            "sources": [
                {
                    "type": "archive",
                    "url": url,
                    "sha256": checksum,
                },
            ],
        }
        writeFile(outFile, json.dumps(module, indent=4) + "\n")
    except Exception as exc:
        print("Generate Enchant Module: FAILED")
        print("")
        print(str(exc))
        sys.exit(1)

    print("")


def processDependencies(bldDir: Path, qtVersion: str) -> None:
    """Generate the pypi-deps.json file listing the flatpak build's PyPI
    dependencies, i.e. everything not already provided by the PyQt BaseApp.
    """
    print("Generate PyPI Dependencies")
    print("==========================")
    print("")

    genScript = bldDir / "flatpak-pip-generator.py"
    outFile = bldDir / "pypi-deps"

    try:
        print(f"Downloading: {PIP_GENERATOR_URL}")
        urllib.request.urlretrieve(PIP_GENERATOR_URL, genScript)
        print("")
        subprocess.run(
            [
                "uv",
                "run",
                str(genScript),
                "--pyproject-file",
                str(ROOT_DIR / "pyproject.toml"),
                "--ignore-pkg",
                "pyqt6",
                "--runtime",
                f"{PYQT_BASEAPP_ID}//{qtVersion}",
                "-o",
                str(outFile),
            ],
            check=True,
        )
    except Exception as exc:
        print("Generate PyPI Dependencies: FAILED")
        print("")
        print(str(exc))
        sys.exit(1)
    finally:
        genScript.unlink(missing_ok=True)

    print("")


def flatpak(args: argparse.Namespace) -> None:
    """Build a flatpak bundle locally (not for flathub)."""
    print("")
    print("Build Flatpak")
    print("=============")
    print("")

    qtVersion: str = args.qt

    numVers, _, relDate = extractVersion()
    pkgVers = stripVersion(numVers)
    relDate = datetime.datetime.strptime(relDate, "%Y-%m-%d")

    bldDir = ROOT_DIR / "dist_flatpak"
    bldPkg = f"novelwriter_{pkgVers}"
    outDir = bldDir / bldPkg

    # Set Up Folders
    # ==============

    if outDir.exists():
        print("Removing old build files ...")
        print("")
        shutil.rmtree(outDir)

    bldDir.mkdir(exist_ok=True)
    outDir.mkdir(exist_ok=True)

    processDependencies(bldDir, qtVersion)
    processEnchant(bldDir)
    writeFile(bldDir / "novelwriter.appdata.xml", appdataXml())

    template = readFile(ROOT_DIR / "setup" / "flatpak" / "io.novelwriter.novelwriter.yml")
    manifestFile = bldDir / "io.novelwriter.novelwriter.yml"
    writeFile(manifestFile, template.replace("@QT_VERSION@", qtVersion))

    # Build flatpak
    # ==============

    manifestPath = str(manifestFile)
    bundleFile = bldDir / f"novelWriter-{pkgVers}-linux.flatpak"

    try:
        subprocess.run(
            [
                "flatpak-builder",
                f"--repo={outDir}/repo",
                "--install-deps-from=flathub",
                "--force-clean",
                outDir,
                manifestPath,
            ],
            check=True,
        )
        subprocess.run(
            [
                "flatpak",
                "build-bundle",
                f"{outDir}/repo",
                bundleFile,
                "io.novelwriter.novelwriter",
            ],
            check=True,
        )
    except Exception as exc:
        print("Flatpak build: FAILED")
        print("")
        print(str(exc))
        print("")
        print("Dependencies:")
        print(" * flatpak flatpak-builder")
        print("")
        sys.exit(1)

    shaFile = makeCheckSum(bundleFile.name, cwd=bldDir)

    toUpload(bundleFile)
    toUpload(shaFile)
