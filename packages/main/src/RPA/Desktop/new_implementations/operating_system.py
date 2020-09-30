import datetime
import getpass
import os
import platform
import signal
import socket
from abc import ABCMeta
from collections import OrderedDict
from typing import Any

from RPA.Desktop.new_implementations.shared_abc import SharedAbc
from RPA.core.decorators import operating_system_required

from . import windows as Windows

if platform.system() == "Windows":
    import psutil
    from psutil._common import bytes2human
else:
    psutil = object
    bytes2human = object


class OperatingSystem(SharedAbc, metaclass=ABCMeta):
    """RPA Framework library containing cross platform keywords for managing
    computer properties and actions.
    """

    @operating_system_required("Windows")
    def get_boot_time(
        self, as_datetime: bool = False, datetime_format: str = "%Y-%m-%d %H:%M:%S"
    ) -> str:
        """Get computer boot time in seconds from Epoch or in datetime string.

        :param as_datetime: if True returns datetime string, otherwise seconds,
            defaults to False
        :param datetime_format: datetime string format, defaults to "%Y-%m-%d %H:%M:%S"
        :return: seconds from Epoch or datetime string

        Example:

        .. code-block:: robotframework

            ${boottime}  Get Boot Time
            ${boottime}  Get Boot Time   as_datetime=True
            ${boottime}  Get Boot Time   as_datetime=True  datetime_format=%d.%m.%Y

        """
        btime = self.boot_time_in_seconds_from_epoch()
        if as_datetime:
            return datetime.datetime.fromtimestamp(btime).strftime(datetime_format)
        return btime

    @operating_system_required("Windows")
    def boot_time_in_seconds_from_epoch(self) -> str:
        """Get machine boot time

        :return: boot time in seconds from Epoch

        Example:

        .. code-block:: robotframework

            ${epoch}  Boot Time In Seconds From Epoch

        """
        return psutil.boot_time()

    def get_machine_name(self) -> str:
        """Get machine name

        :return: machine name as string

        Example:

        .. code-block:: robotframework

            ${machine}  Get Machine Name

        """
        return socket.gethostname()

    def get_username(self) -> str:
        """Get username of logged in user

        :return: username as string

        Example:

        .. code-block:: robotframework

            ${user}  Get Username

        """
        return getpass.getuser()

    @operating_system_required("Darwin", "Linux")
    def put_system_to_sleep(self) -> None:
        """Puts system to sleep mode

        Example:

        .. code-block:: robotframework

            Put System To Sleep

        """
        if platform.system() == "Darwin":
            os.system("pmset sleepnow")
        if platform.system() == "Linux":
            os.system("systemctl suspend")

    @operating_system_required("Windows")
    def process_exists(self, process_name: str, strict: bool = True) -> Any:
        """Check if process exists by its name

                :param process_name: search for this process
                :param strict: defines how match is made, default `True`
                 which means that process name needs to be exact match
                 and `False` does inclusive matching
                :return: process instance or False

                Example:

                .. code-block:: robotframework
        w
                    ${process}  Process Exists  calc
                    ${process}  Process Exists  calc  strict=False

        """
        for p in psutil.process_iter():
            p_name = p.name()
            if strict and process_name.lower() == p_name.lower():
                return p
            elif not strict and process_name.lower() in p_name.lower():
                return p
        return False

    @operating_system_required("Windows")
    def kill_process(self, process_name: str) -> bool:
        """Kill process by name

        :param process_name: name of the process
        :return: True if succeeds False if not

        Example:

        .. code-block:: robotframework

            ${process}  Process Exists  calc  strict=False
            ${status}   Kill Process    ${process.name()}

        """
        p = self.process_exists(process_name)
        if p:
            p.terminate()
            return True
        return False

    @operating_system_required("Windows")
    def kill_process_by_pid(self, pid: int) -> None:
        """Kill process by pid

        :param pid: process identifier

        Example:

        .. code-block:: robotframework

            ${process}  Process Exists  calc  strict=False
            ${status}   Kill Process    ${process.pid}

        """
        os.kill(pid, signal.SIGTERM)

    @operating_system_required("Windows")
    def get_memory_stats(self, humanized: bool = True) -> dict:
        """Get computer memory stats and return those in bytes
        or in humanized memory format.

        :param humanized: if False returns memory information in bytes, defaults to True
        :return: memory information in dictionary format

        Example:

        .. code-block:: robotframework

            &{mem}     Get Memory Stats
            &{mem}     Get Memory Stats   humanized=False

        """
        meminfo = psutil.virtual_memory()
        memdict = meminfo._asdict()
        if humanized:
            humandict = {}
            for key, val in memdict.items():
                if key == "percent":
                    humandict[key] = val
                else:
                    humandict[key] = bytes2human(val)
            return OrderedDict(humandict)
        return memdict

    def connect_by_pid(self, app_pid: str, windowtitle: str = None) -> Any:
        """Connect to application by its pid

        :param app_pid: process id of the application

        Example:

        .. code-block:: robotframework

            ${appid}  Connect By PID  3231

        """
        self.logger.info("Connect to application pid: %s", app_pid)
        window_list = self.get_window_list()
        for win in window_list:
            if win["pid"] == app_pid:
                if windowtitle is None or (windowtitle and windowtitle in win["title"]):
                    self.logger.info(
                        "PID:%s matched window title:%s", win["pid"], win["title"]
                    )
                    return self.connect_by_handle(win["handle"], windowtitle)
        return None

    def connect_by_handle(
        self, handle: str, windowtitle: str = None, existing_app: bool = False
    ) -> Any:
        """Connect to application by its handle

        :param handle: handle of the application

        Example:

        .. code-block:: robotframework

            ${appid}  Connect By Handle  88112

        """
        self.logger.info("Connect to application handle: %s", handle)
        app_instance = None
        app = pywinauto.Application(backend=self._backend).connect(
            handle=handle, visible_only=False
        )
        self.dlg = app.window(handle=handle)
        self.dlg.restore()
        params = None
        if not existing_app:
            if windowtitle is not None:
                params = {"windowtitle": windowtitle}
            app_instance = self._add_app_instance(app=app, params=params, dialog=False)
        return app_instance
