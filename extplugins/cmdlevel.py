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
# 2010-09-26 - 1.0 - BlackMamba
#  using level name instead of level is possible
#  checking if level exists
#  added debug messages
#
# 2010-09-19 - 0.1.0 - BlackMamba
#  Initial version
#

__version__ = '1.0'
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
		m = re.match('^([a-z0-9]+) ([0-9a-z]+)-?([0-9a-z]*)$', data, re.I)
		if not m:
			client.message('^7Invalid parameters')
			self.debug('Options do not fulfill the requirements - matching failed')
			return False
		cmd = m.group(1)
		levelStr = m.group(2)
		if re.match('^[a-z]+$', levelStr, re.I):
			level1 = self.getLevelFromDB(levelStr)
		else:
			level1 = int(level1Str)
			self.checkLevel(level1)
		if len(m.group(3))>0:
			levelStr = m.group(3)
			if re.match('^[a-z]+$', levelStr, re.I):
				level2 = self.getLevelFromDB(levelStr)
			else:
				level2 = int(levelStr)
				self.checkLevel(level2)
		else:
			level2 = 100
		if level1 > level2:
			client.message('^7Invalid parameters')
			self.debug('First level muss be greater than or equal second level')
			return False

		level = str(level1)+'-'+str(level2)
		try:
			self.setCmdLevel(cmd, level1, level2)
		except Warning, msg:
			client.message(str(msg))
			self.debug(str(msg))
		except KeyError, msg:
			client.message(str(msg))
			self.debug(str(msg))
		except Exception, msg:
			client.message('^7Error setting level for %s: %s' % (cmd, str(msg)))
			self.debug(str(msg))
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
			raise Warning, '^7Command %s has already level %s' % (command.command, str(level1)+'-'+str(level2))
			return True
		else:
			self.debug('Set level of %s to %s' % (command.command, str(level1)+'-'+str(level2)))
			command.level = (level1, level2)
			if command.plugin.config.fileName is None or command.plugin.config.fileName == '' or not os.path.exists(command.plugin.config.fileName) or not os.path.isfile(command.plugin.config.fileName):
				self.debug('Could not open config file %s' %command.plugin.config.fileName)
				raise Warning, '^7Could not write to config file'
				return True
			self.loadConfigFile(command.plugin.config.fileName)
			if level2 == 100:
				level = str(level1)
			else:
				level = str(level1)+'-'+str(level2)
			self.changeXML(command.command,level)
			self.writeConfigFile(command.plugin.config.fileName)
			return True


	def loadConfigFile(self, file):
		self.debug('Read file %s' % file)
		filehandle = open(file, 'r')
		self.xml = xml.dom.minidom.parse(filehandle)
		filehandle.close()


	def writeConfigFile(self, file):
		self.debug('Write file %s' % file)
		filehandle = open(file,'w')
		filehandle.write(self.xml.toxml())
		filehandle.close()


	def changeXML(self, cmd, level):
		changed = 0
		if len(self.xml.childNodes) < 1:
			return
		for conf in self.xml.getElementsByTagName('configuration'):
			if conf.nodeType == conf.ELEMENT_NODE:
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
							self.debug('Added a node for the command')
					if changed == 0:
						node = self.createCmdNode()
						node.appendChild(self.createCmdLevelNode(cmd,level))
						conf.appendChild(node)
						changed = 1
						self.debug('Added section "commands" and a node for the command')
		if changed == 0:
			self.debug('Could not change XML')
		else:
			self.debug('Changed XML')


	def createCmdNode(self):
		impl = xml.dom.getDOMImplementation()
		newdoc = impl.createDocument(None, 'nt', None)
		node = newdoc.createElement('settings')
		node.setAttribute('name','commands')
		return node


	def createCmdLevelNode(self, cmd, level):
		impl = xml.dom.getDOMImplementation()
		newdoc = impl.createDocument(None, 'nt', None)
		node = newdoc.createElement('set')
		node.setAttribute('name',cmd)
		text = newdoc.createTextNode(level)
		node.appendChild(text)
		return node

	def getLevelFromDB(self, levelname):
		q = 'SELECT level FROM groups WHERE keyword = "%s"' % levelname
		self.debug('query: %s' % q)
		cursor = self.console.storage.query(q)
		if cursor and cursor.rowcount > 0:
			r = cursor.getRow();
			self.debug('level name %s is level %s' % (levelname, r['level']))
			return int(r['level'])
		else:
			raise KeyError, '^7Could not find level name'

	def checkLevel(self, level):
		q = 'SELECT level FROM groups WHERE level = %s' % levelname
		self.debug('query: %s' % q)
		cursor = self.console.storage.query(q)
		if cursor and cursor.rowcount > 0:
			self.debug('Find level %s' %level)
			return True
		else:
			raise KeyError, '^7Could not find level'
			self.debug('Could not find level %s' % level)
