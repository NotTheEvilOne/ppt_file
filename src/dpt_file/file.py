# -*- coding: utf-8 -*-

"""
direct Python Toolbox
All-in-one toolbox to encapsulate Python runtime variants
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
https://www.direct-netware.de/redirect?dpt;file

This Source Code Form is subject to the terms of the Mozilla Public License,
v. 2.0. If a copy of the MPL was not distributed with this file, You can
obtain one at http://mozilla.org/MPL/2.0/.
----------------------------------------------------------------------------
https://www.direct-netware.de/redirect?licenses;mpl2
----------------------------------------------------------------------------
#echo(dptFileVersion)#
#echo(__FILEPATH__)#
"""

# pylint: disable=import-error,invalid-name,no-member,undefined-variable

from os import path
from weakref import proxy, ProxyTypes
import os
import stat
import time

try:
    import fcntl
    _USE_FILE_LOCKING = False
except ImportError: _USE_FILE_LOCKING = True

try:
    _PY_BYTES = unicode.encode
    _PY_BYTES_TYPE = str
    _PY_STR = unicode.encode
    _PY_UNICODE_TYPE = unicode
except NameError:
    _PY_BYTES = str.encode
    _PY_BYTES_TYPE = bytes
    _PY_STR = bytes.decode
    _PY_UNICODE_TYPE = str
#

_PathLike = (os.PathLike if (hasattr(os, "PathLike")) else object)

class File(_PathLike):
    """
Get file objects to work with files easily.

:author:     direct Netware Group et al.
:copyright:  direct Netware Group - All rights reserved
:package:    dpt
:subpackage: file
:since:      v1.0.0
:license:    https://www.direct-netware.de/redirect?licenses;mpl2
             Mozilla Public License, v. 2.0
    """

    # pylint: disable=bad-option-value,slots-on-old-class
    __slots__ = [ "binary",
                  "chmod",
                  "file_path_name",
                  "file_size",
                  "_handle",
                  "_handle_lock",
                  "_log_handler",
                  "readonly",
                  "timeout_retries",
                  "umask"
                ]
    """
python.org: __slots__ reserves space for the declared variables and prevents
the automatic creation of __dict__ and __weakref__ for each instance.
    """

    def __init__(self, default_umask = None, default_chmod = None, timeout_retries = 5, log_handler = None):
        """
Constructor __init__(File)

:param default_umask: umask to set before creating a new file
:param default_chmod: chmod to set when creating a new file
:param timeout_retries: Retries before timing out
:param log_handler: Log handler to use

:since: v1.0.0
        """

        self.binary = False
        """
Binary file flag
        """
        self.chmod = None
        """
chmod to set when creating a new file
        """
        self.file_path_name = ""
        """
File path and name for the file handle
        """
        self.file_size = -1
        """
File size of the file handle
        """
        self._handle = None
        """
Handle to the opened file
        """
        self._handle_lock = "r"
        """
Current locking mode
        """
        self._log_handler = None
        """
The log handler is called whenever debug messages should be logged or errors
happened.
        """
        self.readonly = False
        """
True if file is opened read-only
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

        if (log_handler is not None): self.log_handler = log_handler
    #

    def __del__(self):
        """
Destructor __del__(File)

:since: v1.0.0
        """

        self.close()
    #

    def __enter__(self):
        """
python.org: Enter the runtime context related to this object.

:since: v1.0.0
        """

        if (self._handle is None): raise IOError("Failed to enter context for an uninitialized file instance")
    #

    def __exit__(self, exc_type, exc_value, traceback):
        """
python.org: Exit the runtime context related to this object.

:return: (bool) True to suppress exceptions
:since:  v1.0.0
        """

        self.close()
    #

    def __fspath__(self):
        """
python.org: Return the file system path representation of the object.

:return: (str) File system path representation
:since:  v1.0.0
        """

        if (self._handle is None): raise IOError("File handle invalid")
        return self.file_path_name
    #

    @property
    def handle(self):
        """
Returns the file handle.

:return: (mixed) File handle; None if not opened
:since:  v1.0.0
        """

        return (None if (self._handle is None) else self._handle)
    #

    @property
    def is_eof(self):
        """
Returns true if the handle is at EOF.

:return: (bool) True if EOF
:since:  v1.0.0
        """

        return (True if (self._handle is None or self._handle.tell() == self.file_size) else False)
    #

    @property
    def is_valid(self):
        """
Returns true if the file handle is available.

:return: (bool) True on success
:since:  v1.0.0
        """

        return (self._handle is not None)
    #

    @property
    def log_handler(self):
        """
Returns the log handler.

:return: (object) Log handler in use
:since:  v1.0.0
        """

        return self._log_handler
    #

    @log_handler.setter
    def log_handler(self, log_handler):
        """
Sets the log handler.

:param log_handler: Log handler to use

:since: v1.0.0
        """

        self._log_handler = (log_handler if (isinstance(log_handler, ProxyTypes)) else proxy(log_handler))
    #

    @property
    def size(self):
        """
Returns the size in bytes.

:return: (int) Size in bytes
:since:  v1.0.0
        """

        return (-1 if (self._handle is None) else self.file_size)
    #

    def close(self, delete_empty = False):
        """
python.org: Flush and close this stream.

:param delete_empty: If the file handle is valid, the file is empty and
                     this parameter is true then the file will be deleted.

:return: (bool) True on success
:since:  v1.0.0
        """

        # global: _USE_FILE_LOCKING

        if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -file.close()- (#echo(__LINE__)#)")
        _return = False

        if (self._handle is not None):
            file_position = self.tell()

            if ((not self.readonly) and delete_empty and file_position < 1):
                self.read(1)
                file_position = self.tell()
            #

            self._handle.close()
            _return = True

            if (self._handle_lock == "w" and _USE_FILE_LOCKING):
                lock_path_name_os = path.normpath("{0}.lock".format(self.file_path_name))

                if (path.exists(lock_path_name_os)):
                    try: os.unlink(lock_path_name_os)
                    except IOError: pass
                #
            #

            if ((not self.readonly) and delete_empty and file_position < 1):
                file_path_name_os = path.normpath(self.file_path_name)
                _return = True

                try: os.unlink(file_path_name_os)
                except IOError: _return = False
            #

            self._handle = None

            self.file_path_name = ""
            self.file_size = -1
            self.readonly = False
        #

        return _return
    #

    def flush(self):
        """
python.org: Flush the write buffers of the stream if applicable.

:return: (bool) True on success
:since:  v1.0.0
        """

        _return = False

        if (self._handle is not None):
            _return = True

            if (not self.readonly):
                self._handle.flush()
                os.fsync(self._handle.fileno())
            #
        #

        return _return
    #

    def lock(self, lock_mode):
        """
Changes file locking if needed.

:param lock_mode: The requested file locking mode ("r" or "w").

:return: (bool) True on success
:since:  v1.0.0
        """

        if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -file.lock({0})- (#echo(__LINE__)#)", lock_mode)

        _return = False

        if (self._handle is None):
            if (self._log_handler is not None): self._log_handler.warning("#echo(__FILEPATH__)# -file.lock()- reporting: File handle invalid")
        elif (lock_mode == "w" and self.readonly):
            if (self._log_handler is not None): self._log_handler.error("#echo(__FILEPATH__)# -file.lock()- reporting: File handle is in readonly mode")
        elif (lock_mode == self._handle_lock): _return = True
        else:
            timeout_retries = self.timeout_retries

            while (timeout_retries > 0):
                if (self._locking(lock_mode)):
                    self._handle_lock = ("w" if (lock_mode == "w") else "r")
                    _return = True
                    timeout_retries = -1

                    break
                else:
                    timeout_retries -= 1
                    time.sleep(1)
                #
            #

            if (timeout_retries > -1 and self._log_handler is not None): self._log_handler.error("#echo(__FILEPATH__)# -file.lock()- reporting: File lock change failed")
        #

        return _return
    #

    def _locking(self, lock_mode, file_path_name = ""):
        """
Runs flock or an alternative locking mechanism.

:param lock_mode: The requested file locking mode ("r" or "w").
:param file_path_name: Alternative path to the locking file (used for
                      _USE_FILE_LOCKING)

:return: (bool) True on success
:since:  v1.0.0
        """

        # global: _PY_STR, _PY_UNICODE_TYPE, _USE_FILE_LOCKING
        # pylint: disable=broad-except

        if (str is not _PY_UNICODE_TYPE and type(file_path_name) is _PY_UNICODE_TYPE): file_path_name = _PY_STR(file_path_name, "utf-8")

        _return = False

        if (len(file_path_name) < 1): file_path_name = self.file_path_name
        lock_path_name_os = path.normpath("{0}.lock".format(file_path_name))

        if (len(file_path_name) > 0 and self._handle is not None):
            if (lock_mode == "w" and self.readonly): _return = False
            elif (_USE_FILE_LOCKING):
                is_locked = path.exists(lock_path_name_os)

                if (is_locked):
                    is_locked = False

                    if ((time.time() - self.timeout_retries) < path.getmtime(lock_path_name_os)):
                        try: os.unlink(lock_path_name_os)
                        except IOError: pass
                    else: is_locked = True
                #

                if (lock_mode == "w"):
                    if (is_locked and self._handle_lock == "w"): _return = True
                    elif (not is_locked):
                        try:
                            open(lock_path_name_os, "w").close()
                            _return = True
                        except IOError: pass
                    #
                elif (is_locked and self._handle_lock == "w"):
                    try:
                        os.unlink(lock_path_name_os)
                        _return = True
                    except IOError: pass
                elif (not is_locked): _return = True
            else:
                operation = (fcntl.LOCK_EX if (lock_mode == "w") else fcntl.LOCK_SH)

                try:
                    fcntl.flock(self._handle, operation)
                    _return = True
                except Exception: pass
            #
        #

        return _return
    #

    def open(self, file_path_name, readonly = False, file_mode = "a+b"):
        """
Opens a file session.

:param file_path_name: Path to the requested file
:param readonly: Open file in readonly mode
:param file_mode: File mode to use

:return: (bool) True on success
:since:  v1.0.0
        """

        # global: _PY_BYTES_TYPE, _PY_STR, _PY_UNICODE_TYPE

        if (str is not _PY_UNICODE_TYPE and type(file_path_name) is _PY_UNICODE_TYPE): file_path_name = _PY_STR(file_path_name, "utf-8")

        if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -file.open({0}, {1})- (#echo(__LINE__)#)", file_path_name, file_mode)

        if (self._handle is None):
            exists = False
            file_path_name_os = path.normpath(file_path_name)
            _return = True

            self.readonly = (True if (readonly) else False)

            if (path.exists(file_path_name_os)): exists = True
            elif (not self.readonly):
                if (self.umask is not None): os.umask(int(self.umask, 8))
            else: _return = False

            is_binary = (True if ("b" in file_mode and bytes == _PY_BYTES_TYPE) else False)

            if (_return):
                try: self._handle = self._open(file_path_name, file_mode, is_binary)
                except IOError: _return = False
            elif (self._log_handler is not None): self._log_handler.warning("#echo(__FILEPATH__)# -file.open()- reporting: Failed opening {0} - file does not exist", file_path_name)

            if (self._handle is None):
                if ((not exists) and (not self.readonly)):
                    try: os.unlink(file_path_name_os)
                    except IOError: pass
                #
            else:
                self.binary = is_binary

                if (self.chmod is not None and (not exists)): os.chmod(file_path_name_os, self.chmod)
                self.file_path_name = file_path_name

                if (self.lock("r")): self.file_size = os.stat(file_path_name_os).st_size
                else:
                    _return = False
                    self.close(not exists)
                    self._handle = None
                #
            #
        else: _return = False

        return _return
    #

    def _open(self, file_path_name_os, file_mode, is_binary):
        """
Opens a file handle and sets the encoding to UTF-8.

:param file_path_name_os: Path to the requested file
:param file_mode: File mode to use
:param is_binary: False if the file is an UTF-8 (or ASCII) encoded one

:return: (object) File
:since:  v1.0.0
        """

        _return = None

        if (not is_binary):
            try: _return = open(file_path_name_os, file_mode, encoding = "utf-8")
            except TypeError: pass
        #

        if (_return is None): _return = open(file_path_name_os, file_mode)
        return _return
    #

    def read(self, n = 0, timeout = -1):
        """
python.org: Read up to n bytes from the object and return them.

:param n: How many bytes to read from the current position (0 means until
          EOF)
:param timeout: Timeout to use (defaults to construction time value)

:return: (bytes) Data; None if EOF
:since:  v1.0.0
        """

        # global: _PY_BYTES_TYPE

        if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -file.read({0:d}, {1:d})- (#echo(__LINE__)#)", n, timeout)

        _return = None

        if (self.lock("r")):
            bytes_unread = n
            timeout_time = time.time()

            _return = (_PY_BYTES_TYPE() if (self.binary) else "")
            timeout_time += (self.timeout_retries if (timeout < 0) else timeout)

            while ((bytes_unread > 0 or n == 0) and (not self.is_eof) and time.time() < timeout_time):
                part_size = (16384 if (bytes_unread > 16384 or n == 0) else bytes_unread)
                _return += self._handle.read(part_size)
                if (n > 0): bytes_unread -= part_size
            #

            if ((bytes_unread > 0 or (n == 0 and self.is_eof))
                and self._log_handler is not None
               ): self._log_handler.error("#echo(__FILEPATH__)# -file.read()- reporting: Timeout occured before EOF")
        #

        return _return
    #

    def seek(self, offset):
        """
python.org: Change the stream position to the given byte offset.

:param offset: Seek to the given offset

:return: (int) Return the new absolute position.
:since:  v1.0.0
        """

        if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -file.seek({0:d})- (#echo(__LINE__)#)", offset)
        return (-1 if (self._handle is None) else self._handle.seek(offset))
    #

    def tell(self):
        """
python.org: Return the current stream position as an opaque number.

:return: (int) Stream position
:since:  v1.0.0
        """

        return (-1 if (self._handle is None) else self._handle.tell())
    #

    def truncate(self, new_size):
        """
python.org: Resize the stream to the given size in bytes.

:param new_size: Cut file at the given byte position

:return: (int) New file size
:since:  v1.0.0
        """

        if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -file.truncate({0:d})- (#echo(__LINE__)#)", new_size)

        if (self.lock("w")):
            _return = self._handle.truncate(new_size)
            self.file_size = new_size
        else: raise IOError("Failed to truncate the file")

        return _return
    #

    def write(self, b, timeout = -1):
        """
python.org: Write the given bytes or bytearray object, b, to the underlying
raw stream and return the number of bytes written.

:param b: (Over)write file with the given data at the current position
:param timeout: Timeout to use (defaults to construction time value)

:return: (int) Number of bytes written
:since:  v1.0.0
        """

        # global: _PY_BYTES, _PY_BYTES_TYPE

        if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -file.write({0:d})- (#echo(__LINE__)#)", timeout)

        _return = 0

        if (self.lock("w")):
            if (self.binary and type(b) is not _PY_BYTES_TYPE): b = _PY_BYTES(b, "raw_unicode_escape")
            bytes_unwritten = len(b)
            bytes_written = self._handle.tell()

            if ((bytes_written + bytes_unwritten) <= self.file_size): new_size = 0
            else: new_size = (bytes_written + bytes_unwritten)

            timeout_time = time.time()
            timeout_time += (self.timeout_retries if (timeout < 0) else timeout)

            while (bytes_unwritten > 0 and time.time() < timeout_time):
                part_size = (16384 if (bytes_unwritten > 16384) else bytes_unwritten)

                self._handle.write(b[_return:(_return + part_size)])
                bytes_unwritten -= part_size
                _return += part_size
            #

            if (bytes_unwritten > 0):
                self.file_size = os.stat(path.normpath(self.file_path_name)).st_size
                if (self._log_handler is not None): self._log_handler.error("#echo(__FILEPATH__)# -file.write()- reporting: Timeout occured before EOF")
            elif (new_size > 0): self.file_size = new_size
        #

        return _return
    #
#
