"""Read-only Windows host CPU/memory observations, sampled once per second."""
import ctypes
import os
import threading
import time
from ctypes import wintypes


class MemoryStatus(ctypes.Structure):
    _fields_ = [('length',wintypes.DWORD),('load',wintypes.DWORD)]+[
        (name,ctypes.c_ulonglong) for name in ['physical','available_physical','pagefile',
        'available_pagefile','virtual','available_virtual','extended_virtual']]


class HostMonitor:
    def __init__(self):
        self.samples = []
        self.stop = threading.Event()
        self.previous = None
        self.error = None
        self.thread = threading.Thread(target=self.run,daemon=True)
        self.kernel = ctypes.WinDLL('kernel32',use_last_error=True) if os.name == 'nt' else None
        if self.kernel is not None:
            self.kernel.GetSystemTimes.argtypes = [ctypes.POINTER(wintypes.FILETIME)]*3
            self.kernel.GetSystemTimes.restype = wintypes.BOOL
            self.kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatus)]
            self.kernel.GlobalMemoryStatusEx.restype = wintypes.BOOL

    def sample(self):
        result = {'monotonic_ns':time.perf_counter_ns()}
        if self.kernel is None:
            result['unavailable'] = 'Windows host monitor only'
            return result
        times = [wintypes.FILETIME() for _ in range(3)]
        if not self.kernel.GetSystemTimes(*(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        values = [value.dwLowDateTime+(value.dwHighDateTime<<32) for value in times]
        if self.previous is not None:
            idle,kernel,user = [n-o for n,o in zip(values,self.previous)]
            result['host_cpu_busy_percent'] = 100*(kernel+user-idle)/max(1,kernel+user)
        self.previous = values
        memory = MemoryStatus();memory.length = ctypes.sizeof(memory)
        if not self.kernel.GlobalMemoryStatusEx(ctypes.byref(memory)):
            raise ctypes.WinError(ctypes.get_last_error())
        result['physical_available_bytes'] = memory.available_physical
        result['physical_total_bytes'] = memory.physical
        return result

    def run(self):
        try:
            while True:
                self.samples.append(self.sample())
                if self.stop.wait(1):break
        except Exception as error:
            self.error = repr(error)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self,*unused):
        self.stop.set();self.thread.join()

    def arrival_samples(self,case):
        start = case['arrival_start_monotonic_ns']
        end = start+int(case['scheduled_seconds']*1e9)
        return {'method':'GetSystemTimes / GlobalMemoryStatusEx, 1 Hz; whole-host observations within timed arrival window; not disk latency or process attribution',
            'error':self.error,'samples':[s for s in self.samples if start <= s['monotonic_ns'] <= end]}
