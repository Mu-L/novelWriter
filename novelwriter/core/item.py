"""
novelWriter – Project Item Class
================================
Data class for a project tree item

File History:
Created: 2018-10-27 [0.0.1]

This file is a part of novelWriter
Copyright 2018–2022, Veronica Berglyd Olsen

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
"""

import logging

from novelwriter.enum import nwItemType, nwItemClass, nwItemLayout
from novelwriter.common import (
    checkInt, isHandle, isItemClass, isItemLayout, isItemType, simplified
)
from novelwriter.constants import nwHeaders, nwLabels, trConst

logger = logging.getLogger(__name__)


class NWItem:

    def __init__(self, theProject):

        self.theProject = theProject

        self._name     = ""
        self._handle   = None
        self._parent   = None
        self._root     = None
        self._order    = 0
        self._type     = nwItemType.NO_TYPE
        self._class    = nwItemClass.NO_CLASS
        self._layout   = nwItemLayout.NO_LAYOUT
        self._status   = None
        self._import   = None
        self._active   = True
        self._expanded = False

        # Document Meta Data
        self._heading   = "H0"  # The main heading
        self._charCount = 0     # Current character count
        self._wordCount = 0     # Current word count
        self._paraCount = 0     # Current paragraph count
        self._cursorPos = 0     # Last cursor position
        self._initCount = 0     # Initial word count

        return

    def __repr__(self):
        return f"<NWItem handle={self._handle}, parent={self._parent}, name='{self._name}'>"

    def __bool__(self):
        return self._handle is not None

    ##
    #  Properties
    ##

    @property
    def itemName(self):
        return self._name

    @property
    def itemHandle(self):
        return self._handle

    @property
    def itemParent(self):
        return self._parent

    @property
    def itemRoot(self):
        return self._root

    @property
    def itemOrder(self):
        return self._order

    @property
    def itemType(self):
        return self._type

    @property
    def itemClass(self):
        return self._class

    @property
    def itemLayout(self):
        return self._layout

    @property
    def itemStatus(self):
        return self._status

    @property
    def itemImport(self):
        return self._import

    @property
    def isActive(self):
        return self._active

    @property
    def isExpanded(self):
        return self._expanded

    @property
    def mainHeading(self):
        return self._heading

    @property
    def charCount(self):
        return self._charCount

    @property
    def wordCount(self):
        return self._wordCount

    @property
    def paraCount(self):
        return self._paraCount

    @property
    def initCount(self):
        return self._initCount

    @property
    def cursorPos(self):
        return self._cursorPos

    ##
    #  Pack/Unpack Data
    ##

    def pack(self):
        """Pack all the data in the class instance into a dictionary.
        """
        item = {}
        meta = {}
        name = {}

        item["handle"]   = str(self._handle)
        item["parent"]   = str(self._parent)
        item["root"]     = str(self._root)
        item["order"]    = str(self._order)
        item["type"]     = str(self._type.name)
        item["class"]    = str(self._class.name)
        meta["expanded"] = str(self._expanded)
        name["status"]   = str(self._status)
        name["import"]   = str(self._import)

        if self._type == nwItemType.FILE:
            item["layout"]    = str(self._layout.name)
            meta["heading"]   = str(self._heading)
            meta["charCount"] = str(self._charCount)
            meta["wordCount"] = str(self._wordCount)
            meta["paraCount"] = str(self._paraCount)
            meta["cursorPos"] = str(self._cursorPos)
            name["active"]    = str(self._active)

        data = {
            "name": str(self._name),
            "itemAttr": item,
            "metaAttr": meta,
            "nameAttr": name,
        }

        return data

    def unpack(self, data):
        """Set the values from a data dictionary.
        """
        if "handle" in data:
            self.setHandle(data["handle"])
        else:
            logger.error("XML item entry does not have a handle")
            return False

        self.setName(data.get("label", ""))
        self.setParent(data.get("parent", None))
        self.setRoot(data.get("root", None))
        self.setOrder(data.get("order", 0))
        self.setType(data.get("type", nwItemType.NO_TYPE))
        self.setClass(data.get("class", nwItemClass.NO_CLASS))
        self.setLayout(data.get("layout", nwItemLayout.NO_LAYOUT))

        self.setExpanded(data.get("expanded", False))
        self.setStatus(data.get("status", None))
        self.setImport(data.get("import", None))
        self.setMainHeading(data.get("heading", "H0"))
        self.setCharCount(data.get("charCount", 0))
        self.setWordCount(data.get("wordCount", 0))
        self.setParaCount(data.get("paraCount", 0))
        self.setCursorPos(data.get("cursorPos", 0))
        self.setActive(data.get("active", True))

        # Make some checks to ensure consistency
        if self._type == nwItemType.ROOT:
            self._root = self._handle  # Root items are their own ancestor
            self._parent = None        # Root items cannot have a parent

        if self._type != nwItemType.FILE:
            self._heading = "H0"  # Only files have headers
            self._active = False  # Can only be True for files
            self._charCount = 0   # Only set for files
            self._wordCount = 0   # Only set for files
            self._paraCount = 0   # Only set for files
            self._cursorPos = 0   # Only set for files

        return True

    ##
    #  Lookup Methods
    ##

    def describeMe(self):
        """Return a string description of the item.
        """
        descKey = "none"
        if self._type == nwItemType.ROOT:
            descKey = "root"
        elif self._type == nwItemType.FOLDER:
            descKey = "folder"
        elif self._type == nwItemType.FILE:
            if self._layout == nwItemLayout.DOCUMENT:
                if self._heading == "H1":
                    descKey = "doc_h1"
                elif self._heading == "H2":
                    descKey = "doc_h2"
                elif self._heading == "H3":
                    descKey = "doc_h3"
                elif self._heading == "H4":
                    descKey = "doc_h4"
                else:
                    descKey = "document"
            elif self._layout == nwItemLayout.NOTE:
                descKey = "note"

        return trConst(nwLabels.ITEM_DESCRIPTION.get(descKey, ""))

    def getImportStatus(self, incIcon=True):
        """Return the relevant importance or status label and icon for
        the current item based on its class.
        """
        if self.isNovelLike():
            stName = self.theProject.data.itemStatus.name(self._status)
            stIcon = self.theProject.data.itemStatus.icon(self._status) if incIcon else None
        else:
            stName = self.theProject.data.itemImport.name(self._import)
            stIcon = self.theProject.data.itemImport.icon(self._import) if incIcon else None
        return stName, stIcon

    ##
    #  Checker Methods
    ##

    def isNovelLike(self):
        """Returns true if the item is of a novel-like class.
        """
        return self._class in (nwItemClass.NOVEL, nwItemClass.ARCHIVE)

    def documentAllowed(self):
        """Returns true if the item is allowed to be of document layout.
        """
        return self._class in (nwItemClass.NOVEL, nwItemClass.ARCHIVE, nwItemClass.TRASH)

    def isInactive(self):
        """Returns true if the item is in an inactive class.
        """
        return self._class in (nwItemClass.NO_CLASS, nwItemClass.ARCHIVE, nwItemClass.TRASH)

    def isRootType(self):
        return self._type == nwItemType.ROOT

    def isFolderType(self):
        return self._type == nwItemType.FOLDER

    def isFileType(self):
        return self._type == nwItemType.FILE

    def isNoteLayout(self):
        return self._layout == nwItemLayout.NOTE

    def isDocumentLayout(self):
        return self._layout == nwItemLayout.DOCUMENT

    ##
    #  Special Setters
    ##

    def setImportStatus(self, value):
        """Update the importance or status value based on class. This is
        a wrapper setter for setStatus and setImport.
        """
        if self.isNovelLike():
            self.setStatus(value)
        else:
            self.setImport(value)
        return

    def setClassDefaults(self, itemClass):
        """Set the default values based on the item's class and the
        project settings.
        """
        if self._parent is not None:
            # Only update for child items
            self.setClass(itemClass)

        if self._layout == nwItemLayout.NO_LAYOUT:
            # If no layout is set, pick one
            if self.isNovelLike():
                self._layout = nwItemLayout.DOCUMENT
            else:
                self._layout = nwItemLayout.NOTE
        elif not self.documentAllowed():
            # Change layout to note if it is not in an allowed folder
            self._layout = nwItemLayout.NOTE

        if self._status is None:
            self.setStatus("New")  # This forces a default value lookup

        if self._import is None:
            self.setImport("New")  # This forces a default value lookup

        return

    ##
    #  Set Item Values
    ##

    def setName(self, name):
        """Set the item name.
        """
        if isinstance(name, str):
            self._name = simplified(name)
        else:
            self._name = ""
        return

    def setHandle(self, handle):
        """Set the item handle, and ensure it is valid.
        """
        if isHandle(handle):
            self._handle = handle
        else:
            self._handle = None
        return

    def setParent(self, handle):
        """Set the parent handle, and ensure it is valid.
        """
        if handle is None:
            self._parent = None
        elif isHandle(handle):
            self._parent = handle
        else:
            self._parent = None
        return

    def setRoot(self, handle):
        """Set the root handle, and ensure it is valid.
        """
        if handle is None:
            self._root = None
        elif isHandle(handle):
            self._root = handle
        else:
            self._root = None
        return

    def setOrder(self, order):
        """Set the item order, and ensure that it is valid. This value
        is purely a meta value, and not actually used by novelWriter at
        the moment.
        """
        self._order = checkInt(order, 0)
        return

    def setType(self, value):
        """Set the item type from either a proper nwItemType, or set it
        from a string representing an nwItemType.
        """
        if isinstance(value, nwItemType):
            self._type = value
        elif isItemType(value):
            self._type = nwItemType[value]
        else:
            logger.error("Unrecognised item type '%s'", value)
            self._type = nwItemType.NO_TYPE
        return

    def setClass(self, value):
        """Set the item class from either a proper nwItemClass, or set
        it from a string representing an nwItemClass.
        """
        if isinstance(value, nwItemClass):
            self._class = value
        elif isItemClass(value):
            self._class = nwItemClass[value]
        else:
            logger.error("Unrecognised item class '%s'", value)
            self._class = nwItemClass.NO_CLASS
        return

    def setLayout(self, value):
        """Set the item layout from either a proper nwItemLayout, or set
        it from a string representing an nwItemLayout.
        """
        if isinstance(value, nwItemLayout):
            self._layout = value
        elif isItemLayout(value):
            self._layout = nwItemLayout[value]
        else:
            logger.error("Unrecognised item layout '%s'", value)
            self._layout = nwItemLayout.NO_LAYOUT
        return

    def setStatus(self, value):
        """Set the item status by looking it up in the valid status
        items of the current project.
        """
        self._status = self.theProject.data.itemStatus.check(value)
        return

    def setImport(self, value):
        """Set the item importance by looking it up in the valid import
        items of the current project.
        """
        self._import = self.theProject.data.itemImport.check(value)
        return

    def setActive(self, state):
        """Set the export flag.
        """
        if isinstance(state, str):
            self._active = (state == str(True))
        else:
            self._active = (state is True)
        return

    def setExpanded(self, state):
        """Set the expanded status of an item in the project tree.
        """
        if isinstance(state, str):
            self._expanded = (state == str(True))
        else:
            self._expanded = (state is True)
        return

    ##
    #  Set Document Meta Data
    ##

    def setMainHeading(self, value):
        """Set the main heading level.
        """
        if value in nwHeaders.H_LEVEL:
            self._heading = value
        return

    def setCharCount(self, count):
        """Set the character count, and ensure that it is an integer.
        """
        if isinstance(count, int):
            self._charCount = max(0, count)
        else:
            self._charCount = 0
        return

    def setWordCount(self, count):
        """Set the word count, and ensure that it is an integer.
        """
        if isinstance(count, int):
            self._wordCount = max(0, count)
        else:
            self._wordCount = 0
        return

    def setParaCount(self, count):
        """Set the paragraph count, and ensure that it is an integer.
        """
        if isinstance(count, int):
            self._paraCount = max(0, count)
        else:
            self._paraCount = 0
        return

    def setCursorPos(self, position):
        """Set the cursor position, and ensure that it is an integer.
        """
        if isinstance(position, int):
            self._cursorPos = max(0, position)
        else:
            self._cursorPos = 0
        return

    def saveInitialCount(self):
        """Save the initial word count.
        """
        self._initCount = self._wordCount
        return

# END Class NWItem
