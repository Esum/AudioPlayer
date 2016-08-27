from ctypes import *
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


class PlayAudio:

    def __init__(self, fmod_system: c_voidp=None, channel: c_voidp=None):
        if fmod_system is None:
            fmod_system = c_voidp()
        FMOD.FMOD_System_Create(byref(fmod_system))
        FMOD.FMOD_System_Init(fmod_system, 1, 0, 0)
        self.system = fmod_system
        
        if channel is None:
            channel = c_voidp()
        self.channel = channel
    
    def play_sound(self, path: str):
        sound = c_voidp()
        FMOD.FMOD_System_CreateStream(self.system, path.encode('ascii'), 0, 0, byref(sound))
        num_subsounds = c_int()
        FMOD.FMOD_Sound_GetNumSubSounds(sound, num_subsounds)

        if num_subsounds.value:
            FMOD.FMOD_Sound_GetSubSound(sound, 0, byref(sound))
        
        FMOD.FMOD_System_PlaySound(self.system, sound, 0, 0, byref(self.channel)) 
    
    def set_position(self, position: int, time_unit: TimeUnit=TimeUnit.ms):
        FMOD.FMOD_Channel_SetPosition(self.channel, position, time_unit)
    
    def stop(self):
        FMOD.FMOD_Channel_Stop(self.channel)
    
    def set_volume(self, volume: float):
        FMOD.FMOD_Channel_SetVolume(self.channel, c_float(volume))