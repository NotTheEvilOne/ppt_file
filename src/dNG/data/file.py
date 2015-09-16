# -*- coding: utf-8 -*-
##j## BOF

"""
file.py
Working with a file abstraction layer
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
https://www.direct-netware.de/redirect?py;file

This Source Code Form is subject to the terms of the Mozilla Public License,
v. 2.0. If a copy of the MPL was not distributed with this file, You can
obtain one at http://mozilla.org/MPL/2.0/.
----------------------------------------------------------------------------
https://www.direct-netware.de/redirect?licenses;mpl2
----------------------------------------------------------------------------
#echo(pyFileVersion)#
#echo(__FILEPATH__)#
"""

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
:license:   https://www.direct-netware.de/redirect?licenses;mpl2
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
		self.resource_file_path_name = ""
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
		self.timeout_retries = (5 if (timeout_retries is None) else timeout_retries)
		"""
Retries before timing out
		"""
		self.umask = default_umask
		"""
umask to set before creating a new file
		"""

		if (default_chmod is None): self.chmod = default_chmod
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
	#

	def close(self, delete_empty = True):
	#
		"""
python.org: Flush and close this stream.

:param delete_empty: If the file handle is valid, the file is empty and
                     this parameter is true then the file will be deleted.

:return: (bool) True on success
:since:  v0.1.00
		"""

		# global: _use_file_locking

		if (self.event_handler is not None): self.event_handler.debug("#echo(__FILEPATH__)# -file.close()- (#echo(__LINE__)#)")
		_return = False

		if (self.resource is not None):
		#
			file_position = self.tell()

			if ((not self.readonly) and delete_empty and file_position < 1):
			#
				self.read(1)
				file_position = self.tell()
			#

			self.resource.close()
			_return = True

			if (self.resource_lock == "w" and _use_file_locking):
			#
				lock_path_name_os = path.normpath("{0}.lock".format(self.resource_file_path_name))

				if (path.exists(lock_path_name_os)):
				#
					try: os.unlink(lock_path_name_os)
					except IOError: pass
				#
			#

			if ((not self.readonly) and delete_empty and file_position < 1):
			#
				file_path_name_os = path.normpath(self.resource_file_path_name)
				_return = True

				try: os.unlink(file_path_name_os)
				except IOError: _return = False
			#

			self.readonly = False
			self.resource = None
			self.resource_file_path_name = ""
			self.resource_file_size = -1
		#

		return _return
	#

	def flush(self):
	#
		"""
python.org: Flush the write buffers of the stream if applicable.

:return: (bool) True on success
:since:  v0.1.00
		"""

		_return = False

		if (self.resource is not None):
		#
			_return = True

			self.resource.flush()
			os.fsync(self.resource.fileno())
		#

		return _return
	#

	def get_handle(self):
	#
		"""
Returns the file pointer.

:return: (mixed) File handle; False on error
:since:  v0.1.00
		"""

		return (False if (self.resource is None) else self.resource)
	#

	def is_eof(self):
	#
		"""
Checks if the pointer is at EOF.

:return: (bool) True on success
:since:  v0.1.00
		"""

		return (True if (self.resource is None or self.resource.tell() == self.resource_file_size) else False)
	#

	def is_resource_valid(self):
	#
		"""
Returns true if the file resource is available.

:return: (bool) True on success
:since:  v0.1.00
		"""

		return (self.resource is not None)
	#

	def lock(self, lock_mode):
	#
		"""
Changes file locking if needed.

:param lock_mode: The requested file locking mode ("r" or "w").

:return: (bool) True on success
:since:  v0.1.00
		"""

		if (self.event_handler is not None): self.event_handler.debug("#echo(__FILEPATH__)# -file.lock({0})- (#echo(__LINE__)#)".format(lock_mode))

		_return = False

		if (self.resource is None):
		#
			if (self.event_handler is not None): self.event_handler.warning("#echo(__FILEPATH__)# -file.lock()- reporting: File resource invalid")
		#
		else:
		#
			if (lock_mode == "w" and self.readonly):
			#
				if (self.event_handler is not None): self.event_handler.error("#echo(__FILEPATH__)# -file.lock()- reporting: File resource is in readonly mode")
			#
			elif (lock_mode == self.resource_lock): _return = True
			else:
			#
				timeout_retries = self.timeout_retries

				while (timeout_retries > 0):
				#
					if (self._locking(lock_mode)):
					#
						self.resource_lock = ("w" if (lock_mode == "w") else "r")
						_return = True
						timeout_retries = -1

						break
					#
					else:
					#
						timeout_retries -= 1
						time.sleep(1)
					#
				#

				if (timeout_retries > -1 and self.event_handler is not None): self.event_handler.error("#echo(__FILEPATH__)# -file.lock()- reporting: File lock change failed")
			#
		#

		return _return
	#

	def _locking(self, lock_mode, file_path_name = ""):
	#
		"""
Runs flock or an alternative locking mechanism.

:param lock_mode: The requested file locking mode ("r" or "w").
:param file_path_name: Alternative path to the locking file (used for
                      _use_file_locking)

:return: (bool) True on success
:since:  v0.1.00
		"""

		# global: _PY_STR, _PY_UNICODE_TYPE, _use_file_locking
		# pylint: disable=broad-except

		if (str is not _PY_UNICODE_TYPE and type(file_path_name) is _PY_UNICODE_TYPE): file_path_name = _PY_STR(file_path_name, "utf-8")

		_return = False

		if (len(file_path_name) < 1): file_path_name = self.resource_file_path_name
		lock_path_name_os = path.normpath("{0}.lock".format(file_path_name))

		if (len(file_path_name) > 0 and self.resource is not None):
		#
			if (lock_mode == "w" and self.readonly): _return = False
			elif (_use_file_locking):
			#
				is_locked = path.exists(lock_path_name_os)

				if (is_locked):
				#
					is_locked = False

					if ((time.time() - self.timeout_retries) < path.getmtime(lock_path_name_os)):
					#
						try: os.unlink(lock_path_name_os)
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
							open(lock_path_name_os, "w").close()
							_return = True
						#
						except IOError: pass
					#
				#
				elif (is_locked and self.resource_lock == "w"):
				#
					try:
					#
						os.unlink(lock_path_name_os)
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

	def open(self, file_path_name, readonly = False, file_mode = "a+b"):
	#
		"""
Opens a file session.

:param file_path_name: Path to the requested file
:param readonly: Open file in readonly mode
:param file_mode: File mode to use

:return: (bool) True on success
:since:  v0.1.00
		"""

		# global: _PY_BYTES_TYPE, _PY_STR, _PY_UNICODE_TYPE

		if (str is not _PY_UNICODE_TYPE and type(file_path_name) is _PY_UNICODE_TYPE): file_path_name = _PY_STR(file_path_name, "utf-8")

		if (self.event_handler is not None): self.event_handler.debug("#echo(__FILEPATH__)# -file.open({0}, {1})- (#echo(__LINE__)#)".format(file_path_name, file_mode))

		if (self.resource is None):
		#
			exists = False
			file_path_name_os = path.normpath(file_path_name)
			_return = True

			self.readonly = (True if (readonly) else False)

			if (path.exists(file_path_name_os)): exists = True
			elif (not self.readonly):
			#
				if (self.umask is not None): os.umask(int(self.umask, 8))
			#
			else: _return = False

			is_binary = (True if ("b" in file_mode and bytes == _PY_BYTES_TYPE) else False)

			if (_return):
			#
				try: self.resource = self._open(file_path_name, file_mode, is_binary)
				except IOError: _return = False
			#
			elif (self.event_handler is not None): self.event_handler.warning("#echo(__FILEPATH__)# -file.open()- reporting: Failed opening {0} - file does not exist".format(file_path_name))

			if (self.resource is None):
			#
				if ((not exists) and (not self.readonly)):
				#
					try: os.unlink(file_path_name_os)
					except IOError: pass
				#
			#
			else:
			#
				self.binary = is_binary

				if (self.chmod is not None and (not exists)): os.chmod(file_path_name_os, self.chmod)
				self.resource_file_path_name = file_path_name

				if (self.lock("r")): self.resource_file_size = path.getsize(file_path_name_os)
				else:
				#
					_return = False
					self.close(not exists)
					self.resource = None
				#
			#
		#
		else: _return = False

		return _return
	#

	def _open(self, file_path_name_os, file_mode, is_binary):
	#
		"""
Opens a file resource and sets the encoding to UTF-8.

:param file_path_name_os: Path to the requested file
:param file_mode: File mode to use
:param is_binary: False if the file is an UTF-8 (or ASCII) encoded one

:return: (object) File
:since:  v0.1.01
		"""

		_return = None

		if (not is_binary):
		#
			try: _return = open(file_path_name_os, file_mode, encoding = "utf-8")
			except TypeError: pass
		#

		if (_return is None): _return = open(file_path_name_os, file_mode)
		return _return
	#

	def read(self, n = 0, timeout = -1):
	#
		"""
python.org: Read up to n bytes from the object and return them.

:param n: How many bytes to read from the current position (0 means until
          EOF)
:param timeout: Timeout to use (defaults to construction time value)

:return: (bytes) Data; None if EOF
:since:  v0.1.00
		"""

		# global: _PY_BYTES_TYPE

		if (self.event_handler is not None): self.event_handler.debug("#echo(__FILEPATH__)# -file.read({0:d}, {1:d})- (#echo(__LINE__)#)".format(n, timeout))

		_return = None

		if (self.lock("r")):
		#
			bytes_unread = n
			timeout_time = time.time()

			_return = (_PY_BYTES_TYPE() if (self.binary) else "")
			timeout_time += (self.timeout_retries if (timeout < 0) else timeout)

			while ((bytes_unread > 0 or n == 0) and (not self.is_eof()) and time.time() < timeout_time):
			#
				part_size = (4096 if (bytes_unread > 4096 or n == 0) else bytes_unread)
				_return += self.resource.read(part_size)
				if (n > 0): bytes_unread -= part_size
			#

			if ((bytes_unread > 0 or (n == 0 and self.is_eof()))
			    and self.event_handler is not None
			   ): self.event_handler.error("#echo(__FILEPATH__)# -file.read()- reporting: Timeout occured before EOF")
		#

		return _return
	#

	def seek(self, offset):
	#
		"""
python.org: Change the stream position to the given byte offset.

:param offset: Seek to the given offset

:return: (int) Return the new absolute position.
:since:  v0.1.00
		"""

		if (self.event_handler is not None): self.event_handler.debug("#echo(__FILEPATH__)# -file.seek({0:d})- (#echo(__LINE__)#)".format(offset))
		return (-1 if (self.resource is None) else self.resource.seek(offset))
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

	def tell(self):
	#
		"""
python.org: Return the current stream position as an opaque number.

:return: (int) Stream position
:since:  v0.1.02
		"""

		return (-1 if (self.resource is None) else self.resource.tell())
	#

	def truncate(self, new_size):
	#
		"""
python.org: Resize the stream to the given size in bytes.

:param new_size: Cut file at the given byte position

:return: (int) New file size
:since:  v0.1.00
		"""

		if (self.event_handler is not None): self.event_handler.debug("#echo(__FILEPATH__)# -file.truncate({0:d})- (#echo(__LINE__)#)".format(new_size))

		if (self.lock("w")):
		#
			_return = self.resource.truncate(new_size)
			self.resource_file_size = new_size
		#
		else: raise IOError("Failed to truncate the file")

		return _return
	#

	def write(self, b, timeout = -1):
	#
		"""
python.org: Write the given bytes or bytearray object, b, to the underlying
raw stream and return the number of bytes written.

:param b: (Over)write file with the given data at the current position
:param timeout: Timeout to use (defaults to construction time value)

:return: (int) Number of bytes written
:since:  v0.1.00
		"""

		# global: _PY_BYTES, _PY_BYTES_TYPE

		if (self.event_handler is not None): self.event_handler.debug("#echo(__FILEPATH__)# -file.write({0:d})- (#echo(__LINE__)#)".format(timeout))

		_return = 0

		if (self.lock("w")):
		#
			if (self.binary and type(b) is not _PY_BYTES_TYPE): b = _PY_BYTES(b, "raw_unicode_escape")
			bytes_unwritten = len(b)
			bytes_written = self.resource.tell()

			if ((bytes_written + bytes_unwritten) <= self.resource_file_size): new_size = 0
			else: new_size = (bytes_written + bytes_unwritten)

			timeout_time = time.time()
			timeout_time += (self.timeout_retries if (timeout < 0) else timeout)

			while (bytes_unwritten > 0 and time.time() < timeout_time):
			#
				part_size = (4096 if (bytes_unwritten > 4096) else bytes_unwritten)

				self.resource.write(b[_return:(_return + part_size)])
				bytes_unwritten -= part_size
				_return += part_size
			#

			if (bytes_unwritten > 0):
			#
				self.resource_file_size = path.getsize(path.normpath(self.resource_file_path_name))
				if (self.event_handler is not None): self.event_handler.error("#echo(__FILEPATH__)# -file.write()- reporting: Timeout occured before EOF")
			#
			elif (new_size > 0): self.resource_file_size = new_size
		#

		return _return
	#
#

##j## EOF