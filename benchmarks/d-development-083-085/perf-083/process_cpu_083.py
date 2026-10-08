"""CPU snapshots on the exact retained task-owned Popen handle, never PID lookup."""
import ctypes
from ctypes import wintypes
class FileTime(ctypes.Structure):
    _fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
def snapshot(process):
    fn=ctypes.WinDLL('kernel32',use_last_error=True).GetProcessTimes
    fn.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FileTime)]*4;fn.restype=wintypes.BOOL
    times=[FileTime() for _ in range(4)]
    assert fn(int(process._handle),*[ctypes.byref(t) for t in times]),ctypes.get_last_error()
    values=[(t.high<<32)|t.low for t in times]
    return {'creation_ticks':values[0],'kernel_ticks':values[2],'user_ticks':values[3]}
def difference(before,after):
    assert before['creation_ticks']==after['creation_ticks'],'Child identity changed'
    kernel=after['kernel_ticks']-before['kernel_ticks'];user=after['user_ticks']-before['user_ticks']
    assert kernel>=0 and user>=0
    return {'kernel_ms':kernel/10000,'user_ms':user/10000,'cpu_ms':(kernel+user)/10000}
