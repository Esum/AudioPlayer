from ctypes import *
from threading import Thread
import time
VERSION = 0x00010810

class FMOD_System:

    def __init__(self):
        self.dll = WinDLL("fmodL")
        fmod_system = c_voidp()
        self.dll.FMOD_System_Create(byref(fmod_system))
        self.dll.FMOD_System_Init(fmod_system, 6, 0, 0)
        self.system = fmod_system

    def play(self, path):
        sound = c_voidp()
        self.dll.FMOD_System_CreateStream(self.system, path.encode('ascii'), 0, 0, byref(sound))
        num_subsounds = c_int()
        self.dll.FMOD_Sound_GetNumSubSounds(sound, num_subsounds)

        if num_subsounds.value:
            threads = []
            for subsound_num in range(num_subsounds.value):
                subsound = c_voidp()
                self.dll.FMOD_Sound_GetSubSound(sound, subsound_num, byref(subsound))
                self.dll.FMOD_System_PlaySound(self.system, subsound, 0, 0, 0)
        else:
            self.dll.FMOD_System_PlaySound(self.system, sound, 0, 0, 0)
        
        for _ in range(0, 100):
            self.dll.FMOD_System_Update(self.system)
            time.sleep(0.050)