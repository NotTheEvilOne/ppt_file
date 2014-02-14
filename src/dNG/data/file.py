# -*- coding: utf-8 -*-
##j## BOF

"""
File functions class to use some advanced locking mechanisms.
"""
"""n// NOTE
----------------------------------------------------------------------------
file.py
Working with a file abstraction layer
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
http://www.direct-netware.de/redirect.py?py;file

This Source Code Form is subject to the terms of the Mozilla Public License,
v. 2.0. If a copy of the MPL was not distributed with this file, You can
obtain one at http://mozilla.org/MPL/2.0/.
----------------------------------------------------------------------------
http://www.direct-netware.de/redirect.py?licenses;mpl2
----------------------------------------------------------------------------
#echo(pyFileVersion)#
#echo(__FILEPATH__)#
----------------------------------------------------------------------------
NOTE_END //n"""

# pylint: disable=import-error,invalid-name,undefined-variable

from os import path
import os
import stat
import time

try:
#
	import fcntl
	_use_file_locking = False
#
except ImportError: _use_file_locking = True

try:
#
	_PY_BYTES = unicode.encode
	_PY_BYTES_TYPE = str
	_PY_STR = unicode.encode
	_PY_UNICODE_TYPE = unicode
#
except NameError:
#
	_PY_BYTES = str.encode
	_PY_BYTES_TYPE = bytes
	_PY_STR = bytes.decode
	_PY_UNICODE_TYPE = str
#

class File(object):
#
	"""
Get file objects to work with files easily.

:author:    direct Netware Group
:copyright: direct Netware Group - All rights reserved
:package:   file.py
:since:     v0.1.00
:license:   http://www.direct-netware.de/redirect.py?licenses;mpl2
            Mozilla Public License, v. 2.0
	"""

	def __init__(self, default_umask = None, default_chmod = None, timeout_retries = 5, event_handler = None):
	#
		"""
Constructor __init__(File)

:param default_umask: umask to set before creating a new file
:param default_chmod: chmod to set when creating a new file
:param timeout_retries: Retries before timing out
:param event_handler: EventHandler to use

:since: v0.1.00
		"""

		self.binary = False
		"""
Binary file flag
		"""
		self.chmod = None
		"""
chmod to set when creating a new file
		"""
		self.event_handler = event_handler
		"""
The EventHandler is called whenever debug messages should be logged or errors
	happened.
		"""
		self.readonly = False
		"""
True if file is opened read-only
		"""
		self.resource = None
		"""
Resource to the opened file
		"""
		self.resource_file_pathname = ""
		"""
Filename for the resource pointer
		"""
		self.resource_file_size = -1
		"""
File size of the resource pointer
		"""
		self.resource_lock = "r"
		"""
Current locking mode
		"""
		self.timeout_retries = (5 if (timeout_retries == None) else timeout_retries)
		"""
Retries before timing out
		"""
		self.umask = default_umask
		"""
umask to set before creating a new file
		"""

		if (default_chmod == None): self.chmod = default_chmod
		else:
		#
			default_chmod = int(default_chmod, 8)
			self.chmod = 0

			if ((1000 & default_chmod) == 1000): self.chmod |= stat.S_ISVTX
			if ((2000 & default_chmod) == 2000): self.chmod |= stat.S_ISGID
			if ((4000 & default_chmod) == 4000): self.chmod |= stat.S_ISUID
			if ((0o100 & default_chmod) == 0o100): self.chmod |= stat.S_IXUSR
			if ((0o200 & default_chmod) == 0o200): self.chmod |= stat.S_IWUSR
			if ((0o400 & default_chmod) == 0o400): self.chmod |= stat.S_IRUSR
			if ((0o010 & default_chmod) == 0o010): self.chmod |= stat.S_IXGRP
			if ((0o020 & default_chmod) == 0o020): self.chmod |= stat.S_IWGRP
			if ((0o040 & default_chmod) == 0o040): self.chmod |= stat.S_IRGRP
			if ((0o001 & default_chmod) == 0o001): self.chmod |= stat.S_IXOTH
			if ((0o002 & default_chmod) == 0o002): self.chmod |= stat.S_IWOTH
			if ((0o004 & default_chmod) == 0o004): self.chmod |= stat.S_IROTH
		#
	#

	def __del__(self):
	#
		"""
Destructor __del__(File)

:since: v0.1.00
		"""

		self.close()
		self.resource = None
	#

	def close(self, delete_empty = True):
	#
		"""
Closes an active file session.

:param delete_empty: If the file handle is valid, the file is empty and
                     this parameter is true then the file will be deleted.

:return: (bool) True on success
:since: v0.1.00
		"""

		# global: _use_file_locking

		if (self.event_handler != None): self.event_handler.debug("#echo(__FILEPATH__)# -file.close(delete_empty)- (#echo(__LINE__)#)")
		_return = False

		if (self.resource != None):
		#
			file_position = self.get_position()

			if ((not self.readonly) and delete_empty and (not file_position)):
			#
				self.read(1)
				file_position = self.get_position()
			#

			self.resource.close()
			_return = True

			if (self.resource_lock == "w" and _use_file_locking):
			#
				lock_pathname_os = path.normpath("{0}.lock".format(self.resource_file_pathname))

				if (path.exists(lock_pathname_os)):
				#
					try: os.unlink(lock_pathname_os)
					except IOError: pass
				#
			#

			if ((not self.readonly) and delete_empty and file_position < 0):
			#
				file_pathname_os = path.normpath(self.resource_file_pathname)
				_return = True

				try: os.unlink(file_pathname_os)
				except IOError: _return = False
			#

			self.readonly = False
			self.resource = None
			self.resource_file_pathname = ""
			self.resource_file_size = -1
		#

		return _return
	#

	def eof_check(self):
	#
		"""
Checks if the pointer is at EOF.

:return: (bool) True on success
:since:  v0.1.00
		"""

		return (True if (self.resource == None or self.resource.tell() == self.resource_file_size) else False)
	#

	def get_handle(self):
	#
		"""
Returns the file pointer.

:return: (mixed) File handle; False on error
:since:  v0.1.00
		"""

		return (False if (self.resource == None) else self.resource)
	#

	def get_position(self):
	#
		"""
Returns the current offset.

:return: (int) Offset; False on error
:since:  v0.1.00
		"""

		return (False if (self.resource == None) else self.resource.tell())
	#

	def lock(self, lock_mode):
	#
		"""
Changes file locking if needed.

:param lock_mode: The requested file locking mode ("r" or "w").

:return: (bool) True on success
:since: v0.1.00
		"""

		if (self.event_handler != None): self.event_handler.debug("#echo(__FILEPATH__)# -file.lock({0})- (#echo(__LINE__)#)".format(lock_mode))

		_return = False

		if (self.resource == None):
		#
			if (self.event_handler != None): self.event_handler.warning("#echo(__FILEPATH__)# -file.lock()- reporting: File resource invalid")
		#
		else:
		#
			if (lock_mode == "w" and self.readonly):
			#
				if (self.event_handler != None): self.event_handler.error("#echo(__FILEPATH__)# -file.lock()- reporting: File resource is in readonly mode")
			#
			elif (lock_mode == self.resource_lock): _return = True
			else:
			#
				timeout_retries = self.timeout_retries

				while (timeout_retries > 0):
				#
					if (self._locking(lock_mode)):
					#
						_return = True
						timeout_retries = -1

						self.resource_lock = ("w" if (lock_mode == "w") else "r")
					#
					else:
					#
						timeout_retries -= 1
						time.sleep(1)
					#
				#

				if (timeout_retries > -1 and self.event_handler != None): self.event_handler.error("#echo(__FILEPATH__)# -file.lock()- reporting: File lock change failed")
			#
		#

		return _return
	#

	def _locking(self, lock_mode, file_pathname = ""):
	#
		"""
Runs flock or an alternative locking mechanism.

:param lock_mode: The requested file locking mode ("r" or "w").
:param file_pathname: Alternative path to the locking file (used for
                      _use_file_locking)

:return: (bool) True on success
:since:  v0.1.00
		"""

		# global: _PY_STR, _PY_UNICODE_TYPE, _use_file_locking
		# pylint: disable=broad-except

		if (str != _PY_UNICODE_TYPE and type(file_pathname) == _PY_UNICODE_TYPE): file_pathname = _PY_STR(file_pathname, "utf-8")

		_return = False

		if (len(file_pathname) < 1): file_pathname = self.resource_file_pathname
		lock_pathname_os = path.normpath("{0}.lock".format(file_pathname))

		if (len(file_pathname) > 0 and self.resource != None):
		#
			if (lock_mode == "w" and self.readonly): _return = False
			elif (_use_file_locking):
			#
				is_locked = path.exists(lock_pathname_os)

				if (is_locked):
				#
					is_locked = False

					if ((time.time() - self.timeout_retries) < path.getmtime(lock_pathname_os)):
					#
						try: os.unlink(lock_pathname_os)
						except IOError: pass
					#
					else: is_locked = True
				#

				if (lock_mode == "w"):
				#
					if (is_locked and self.resource_lock == "w"): _return = True
					elif (not is_locked):
					#
						try:
						#
							open(lock_pathname_os, "w").close()
							_return = True
						#
						except IOError: pass
					#
				#
				elif (is_locked and self.resource_lock == "w"):
				#
					try:
					#
						os.unlink(lock_pathname_os)
						_return = True
					#
					except IOError: pass
				#
				elif (not is_locked): _return = True
			#
			else:
			#
				operation = (fcntl.LOCK_EX if (lock_mode == "w") else fcntl.LOCK_SH)

				try:
				#
					fcntl.flock(self.resource, operation)
					_return = True
				#
				except Exception: pass
			#
		#

		return _return
	#

	def read(self, _bytes = 0, timeout = -1):
	#
		"""
Reads from the current file session.

:param _bytes: How many bytes to read from the current position (0 means
                  until EOF)
:param timeout: Timeout to use (defaults to construction time value)

:return: (mixed) Data; False on error
:since:  v0.1.00
		"""

		# global: _PY_BYTES_TYPE

		if (self.event_handler != None): self.event_handler.debug("#echo(__FILEPATH__)# -file.read({0:d}, {1:d})- (#echo(__LINE__)#)".format(_bytes, timeout))

		_return = False

		if (self.lock("r")):
		#
			bytes_unread = _bytes
			timeout_time = time.time()

			_return = (_PY_BYTES_TYPE() if (self.binary) else "")
			timeout_time += (self.timeout_retries if (timeout < 0) else timeout)

			while ((bytes_unread > 0 or _bytes == 0) and (not self.eof_check()) and time.time() < timeout_time):
			#
				part_size = (4096 if (bytes_unread > 4096 or _bytes == 0) else bytes_unread)
				_return += self.resource.read(part_size)
				if (_bytes > 0): bytes_unread -= part_size
			#

			if ((bytes_unread > 0 or (_bytes == 0 and self.eof_check())) and self.event_handler != None): self.event_handler.error("#echo(__FILEPATH__)# -file.read()- reporting: Timeout occured before EOF")
		#

		return _return
	#

	def resource_check(self):
	#
		"""
Returns true if the file resource is available.

:return: (bool) True on success
:since:  v0.1.00
		"""

		return (False if (self.resource == None) else True)
	#

	def seek(self, offset):
	#
		"""
Seek to a given offset.

:param offset: Seek to the given offset

:return: (bool) True on success
:since:  v0.1.00
		"""

		if (self.event_handler != None): self.event_handler.debug("#echo(__FILEPATH__)# -file.seek({0:d})- (#echo(__LINE__)#)".format(offset))

		if (self.resource == None): return False
		else:
		#
			self.resource.seek(offset)
			return True
		#
	#

	def set_event_handler(self, event_handler = None):
	#
		"""
Sets the EventHandler.

:param event_handler: EventHandler to use

:since: v0.1.00
		"""

		self.event_handler = event_handler
	#

	def truncate(self, new_size):
	#
		"""
Truncates the active file session.

:param new_size: Cut file at the given byte position

:return: (bool) True on success
:since:  v0.1.00
		"""

		if (self.event_handler != None): self.event_handler.debug("#echo(__FILEPATH__)# -file.truncate({0:d})- (#echo(__LINE__)#)".format(new_size))

		if (self.lock("w")):
		#
			self.resource.truncate(new_size)
			self.resource_file_size = new_size
			return True
		#
		else: return False
	#

	def open(self, file_pathname, readonly = False, file_mode = "a+b"):
	#
		"""
Opens a file session.

:param file_pathname: Path to the requested file
:param readonly: Open file in readonly mode
:param file_mode: Filemode to use

:return: (bool) True on success
:since:  v0.1.00
		"""

		# global: _PY_BYTES_TYPE, _PY_STR, _PY_UNICODE_TYPE

		if (str != _PY_UNICODE_TYPE and type(file_pathname) == _PY_UNICODE_TYPE): file_pathname = _PY_STR(file_pathname, "utf-8")

		if (self.event_handler != None): self.event_handler.debug("#echo(__FILEPATH__)# -file.open({0}, readonly, {1})- (#echo(__LINE__)#)".format(file_pathname, file_mode))

		if (self.resource == None):
		#
			exists = False
			file_pathname_os = path.normpath(file_pathname)
			_return = True

			self.readonly = (True if (readonly) else False)

			if (path.exists(file_pathname_os)): exists = True
			elif (not self.readonly):
			#
				if (self.umask != None): os.umask(int(self.umask, 8))
			#
			else: _return = False

			if (_return):
			#
				try: self.resource = open(file_pathname_os, file_mode)
				except IOError: pass
			#
			elif (self.event_handler != None): self.event_handler.warning("#echo(__FILEPATH__)# -file.open()- reporting: Failed opening {0} - file does not exist".format(file_pathname))

			if (self.resource == None):
			#
				if ((not exists) and (not self.readonly)):
				#
					try: os.unlink(file_pathname_os)
					except IOError: pass
				#
			#
			else:
			#
				self.binary = (True if ("b" in file_mode and bytes == _PY_BYTES_TYPE) else False)

				if (self.chmod != None and (not exists)): os.chmod(file_pathname_os, self.chmod)
				self.resource_file_pathname = file_pathname

				if (self.lock("r")): self.resource_file_size = path.getsize(file_pathname_os)
				else:
				#
					self.close(not exists)
					self.resource = None
				#
			#
		#
		else: _return = False

		return _return
	#

	def write(self, data, timeout = -1):
	#
		"""
Write content to the active file session.

:param data: (Over)write file with the data content at the current position
:param timeout: Timeout to use (defaults to construction time value)

:return: (bool) True on success
:since:  v0.1.00
		"""

		# global: _PY_BYTES, _PY_BYTES_TYPE

		if (self.event_handler != None): self.event_handler.debug("#echo(__FILEPATH__)# -file.write(data, {0:d})- (#echo(__LINE__)#)".format(timeout))

		_return = False

		if (self.lock("w")):
		#
			if (self.binary and type(data) != _PY_BYTES_TYPE): data = _PY_BYTES(data, "raw_unicode_escape")
			bytes_unwritten = len(data)
			bytes_written = self.resource.tell()

			if ((bytes_written + bytes_unwritten) > self.resource_file_size): new_size = bytes_written + bytes_unwritten - self.resource_file_size
			else: new_size = 0

			bytes_written = 0
			timeout_time = time.time()
			_return = True

			timeout_time += (self.timeout_retries if (timeout < 0) else timeout)

			while (_return and bytes_unwritten > 0 and time.time() < timeout_time):
			#
				part_size = (4096 if (bytes_unwritten > 4096) else bytes_unwritten)

				try:
				#
					self.resource.write(data[bytes_written:(bytes_written + part_size)])
					bytes_unwritten -= part_size
					bytes_written += part_size
				#
				except IOError: _return = False
			#

			if (bytes_unwritten > 0):
			#
				_return = False
				self.resource_file_size = path.getsize(path.normpath(self.resource_file_pathname))
				if (self.event_handler != None): self.event_handler.error("#echo(__FILEPATH__)# -file.write()- reporting: Timeout occured before EOF")
			#
			elif (new_size > 0): self.resource_file_size = new_size
		#

		return _return
	#
#

##j## EOF