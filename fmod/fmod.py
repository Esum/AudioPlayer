from ctypes import *
from threading import Thread
import time
VERSION = 0x00010810

FMOD = WinDLL("fmodL")


class SystemUpdateThread(Thread):

    def __init__(self, fmod_system: c_voidp):
        super(SystemUpdateThread, self).__init__()
        self.system = fmod_system
    
    def run(self):
        for _ in range(0, 100):
            FMOD.FMOD_System_Update(self.system)
            time.sleep(0.05)


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
        
        FMOD.FMOD_System_PlaySound(self.system, sound, 0, 0, 0)
        
        update_thread = SystemUpdateThread(self.system)
        update_thread.start()

        return update_thread