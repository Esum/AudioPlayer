from ctypes import *
from threading import Thread
import time
from enum import IntEnum
VERSION = 0x00010810

FMOD = WinDLL("fmodL")


class TimeUnit:
    ms = 0x00000001
    pcm = 0x00000002
    pcmbytes = 0x00000004
    rawbytes = 0x00000008
    pcmfraction = 0x00000010
    modorder = 0x00000100
    modrow = 0x00000200
    modpattern = 0x00000400
    buffered = 0x10000000


class SystemUpdateThread(Thread):

    def __init__(self, fmod_system: c_voidp, channel: c_voidp):
        super(SystemUpdateThread, self).__init__()
        self.system = fmod_system
        self.channel = channel
    
    def run(self):
        for _ in range(0, 100):
            FMOD.FMOD_System_Update(self.system)
            time.sleep(0.05)
    
    def set_position(self, position: int, time_unit: TimeUnit=TimeUnit.ms):
        FMOD.FMOD_Channel_SetPosition(self.channel, position, time_unit.value)
    
    def stop(self):
        FMOD.FMOD_Channel_Stop(self.channel)


class FMOD_System:

    def __init__(self):
        FMOD = WinDLL("fmodL")
        fmod_system = c_voidp()
        FMOD.FMOD_System_Create(byref(fmod_system))
        FMOD.FMOD_System_Init(fmod_system, 6, 0, 0)
        self.system = fmod_system

    def play(self, path: str) -> SystemUpdateThread:
        sound = c_voidp()
        FMOD.FMOD_System_CreateStream(self.system, path.encode('ascii'), 0, 0, byref(sound))
        num_subsounds = c_int()
        FMOD.FMOD_Sound_GetNumSubSounds(sound, num_subsounds)

        if num_subsounds.value:
            FMOD.FMOD_Sound_GetSubSound(sound, 0, byref(sound))

        channel = c_voidp()
        
        FMOD.FMOD_System_PlaySound(self.system, sound, 0, 0, byref(channel))
        
        update_thread = SystemUpdateThread(self.system, channel)
        update_thread.start()

        return update_thread