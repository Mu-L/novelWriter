#! /bin/sh
# uses https://github.com/flatpak/flatpak-builder-tools/blob/master/pip/flatpak-pip-generator
curl -LO https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator.py
uv run flatpak-pip-generator.py \
    --pyproject-file=../../pyproject.toml \
    --ignore-pkg=pyqt6 \
    --runtime=com.riverbankcomputing.PyQt.BaseApp//6.11 \
    -o pypi-deps
rm flatpak-pip-generator.py
