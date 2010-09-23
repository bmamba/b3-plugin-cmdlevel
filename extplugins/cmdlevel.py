# CmdLevel - A plugin to change the level of a command
#
# Copyright (C) 2010 BlackMamba
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.
#
# Requirements B3 v1.3+
#
# Changelog:
#
# 09/19/2010 - 0.1.0 - BlackMamba
#  Initial version
#

__version__ = '0.1.0'
__author__ = 'BlackMamba'

import xml.dom.minidom
import string
import b3, os, re
import b3.events
import b3.plugin

class CmdlevelPlugin(b3.plugin.Plugin):

	def startup(self):
		self._adminPlugin = self.console.getPlugin('admin')
		if not self._adminPlugin:
			self.error('Could not find admin plugin')
			return False

		try:
			level_scl = self.config.get('commands','bmshowcmdlevel')
		except:
			level_scl = 60

		try:
			level_cl = self.config.get('commands','bmcmdlevel')
		except:
			level_cl = 100

		self._adminPlugin.registerCommand(self, 'bmcmdlevel', level_cl, self.cmd_cmdlevel,'cmdlevel')
		self._adminPlugin.registerCommand(self, 'bmshowcmdlevel', level_scl, self.cmd_showcmdlevel,'showcmdlevel')

	def cmd_showcmdlevel(self, data, client, cmd=None):
		"""\
		<command> - show level of a command
		"""
		try:
			command = self._adminPlugin._commands[data]
		except:
			client.message('^7Could not find command')
			return False
		client.message("Command level: %s" % str(command.level))

	def cmd_cmdlevel(self, data, client, cmd=None):
		"""\
		<command> <level> - set the level of a command
		"""
		m = re.match('^([a-z]+) ([0-9]+)-?([0-9]*)$', data, re.I)
		if not m:
			client.message('^7Invalid parameters')
			return False

		cmd   = m.group(1)
		level1 = int(m.group(2))
		if len(m.group(3))>0:
			level2 = int(m.group(3))
		else:
			level2 = 100
		if level1 > level2:
			client.message('^7Invalid parameters')
			return False

		level = str(level1)+'-'+str(level2)
		try:
			self.setCmdLevel(cmd, level1, level2)
		except Warning, msg:
			client.message(str(msg))
		except KeyError, msg:
			client.message(str(msg))
		except Exception, msg:
			client.message('^7Error setting level for %s: %s' % (cmd, str(msg)))
		else:
			client.message('^7Command %s set to level %s' % (cmd, level))
			return True

	def setCmdLevel(self, command, level1, level2):
		try:
			command = self._adminPlugin._commands[command]
		except:
			raise KeyError, '^7Could not find command %s' % command
			return False

		if command.level == (level1, level2):
			raise Warning, '^7Command %s is already level %s' % (command.command, str(level1)+'-'+str(level2))
			return True
		else:
			command.level = (level1, level2)
			self.loadConfigFile(command.plugin.config.fileName)
			if level2 == 100:
				level = str(level1)
			else:
				level = str(level1)+'-'+str(level2)
			self.changeXML(command.command,level)
			self.writeConfigFile(command.plugin.config.fileName)
			return True


	def loadConfigFile(self, file):
		filehandle = open(file, "r")
		self.xml = xml.dom.minidom.parse(filehandle)
		filehandle.close()


	def writeConfigFile(self, file):
		filehandle = open(file,"w")
		filehandle.write(self.xml.toxml())
		filehandle.close()


	def changeXML(self, cmd, level):
		changed = 0
		if len(self.xml.childNodes) < 1:
			return
		for conf in self.xml.childNodes:
			if conf.nodeType == conf.ELEMENT_NODE and conf.nodeName == "configuration":
				settings = conf.getElementsByTagName('settings')
				for setting in settings:
					if setting.getAttribute('name') == 'commands':
						sets = setting.getElementsByTagName('set')
						for node in sets:
							if node.getAttribute('name')== cmd:
								command = node.attributes['name'].value
								for textnode in node.childNodes:
									if textnode.nodeType == textnode.TEXT_NODE:
										textnode.data = level
										changed = 1
				if changed == 0:
					for setting in settings:
						if setting.getAttribute('name') == 'commands' and changed == 0:
							setting.appendChild(self.createCmdLevelNode(cmd,level))
							changed = 1
					if changed == 0:
						node = self.createCmdNode()
						node.appendChild(self.createCmdLevelNode(cmd,level))
						conf.appendChild(node)


	def createCmdNode(self):
		impl = xml.dom.getDOMImplementation()
		newdoc = impl.createDocument(None, "nt", None)
		node = newdoc.createElement('settings')
		node.setAttribute('name','commands')
		return node


	def createCmdLevelNode(self, cmd, level):
		impl = xml.dom.getDOMImplementation()
		newdoc = impl.createDocument(None, "nt", None)
		node = newdoc.createElement('set')
		node.setAttribute('name',cmd)
		text = newdoc.createTextNode(level)
		node.appendChild(text)
		return node

