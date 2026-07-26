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
import shutil
import subprocess
import sys

from utils.common import ROOT_DIR, appdataXml, extractVersion, makeCheckSum, stripVersion, toUpload, writeFile


def flatpak(args: argparse.Namespace) -> None:
    """Build a flatpak bundle locally (not for flathub)."""
    print("")
    print("Build flatpak")
    print("==============")
    print("")

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

    writeFile(bldDir / "novelwriter.appdata.xml", appdataXml())

    # Build flatpak
    # ==============

    manifestPath = "setup/flatpak/io.novelwriter.novelwriter.yml"
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
