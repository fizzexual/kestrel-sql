"""Task-owned Windows process peak memory; query retained handle after wait."""
import ctypes
from ctypes import wintypes
class MemoryCounters(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('page_faults',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in
        ['peak_working_set','working_set','quota_peak_paged_pool','quota_paged_pool','quota_peak_nonpaged_pool','quota_nonpaged_pool','pagefile','peak_pagefile']]
def peak_memory(process):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    fn=kernel.K32GetProcessMemoryInfo
    fn.argtypes=[wintypes.HANDLE,ctypes.POINTER(MemoryCounters),wintypes.DWORD]
    fn.restype=wintypes.BOOL
    counters=MemoryCounters();counters.cb=ctypes.sizeof(counters)
    success=bool(fn(int(process._handle),ctypes.byref(counters),counters.cb))
    return {'method':'K32GetProcessMemoryInfo after process.wait, before retained Popen handle release; full process peak includes setup and validation',
        'success':success,'last_error':None if success else ctypes.get_last_error(),
        'peak_working_set_bytes':counters.peak_working_set if success else None,
        'peak_commit_bytes':counters.peak_pagefile if success else None,
        'sources':['https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo',
            'https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters']}
