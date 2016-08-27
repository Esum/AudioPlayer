from ctypes import *
import time
from enum import IntEnum
VERSION = 0x00010810

FMOD = WinDLL("fmodL")


class TimeUnit:
    """
    ms: Milliseconds.
    pcm: PCM samples, related to milliseconds * samplerate / 1000.
    pcmbytes: Bytes, related to PCM samples * channels * datawidth (ie 16bit = 2 bytes).
    rawbytes: Raw file bytes of (compressed) sound data (does not include headers). Only used by Sound::getLength and Channel::getPosition.
    pcmfraction: Fractions of 1 PCM sample. Unsigned int range 0 to 0xFFFFFFFF. Used for sub-sample granularity for DSP purposes.
    modorder: MOD/S3M/XM/IT. Order in a sequenced module format. Use Sound::getFormat to determine the PCM format being decoded to.
    modrow: MOD/S3M/XM/IT. Current row in a sequenced module format. Sound::getLength will return the number of rows in the currently playing or seeked to pattern.
    modpattern: MOD/S3M/XM/IT. Current pattern in a sequenced module format. Sound::getLength will return the number of patterns in the song and Channel::getPosition will return the currently playing pattern.
    buffered: Time value as seen by buffered stream. This is always ahead of audible time, and is only used for processing.
    """
    ms = 0x00000001
    pcm = 0x00000002
    pcmbytes = 0x00000004
    rawbytes = 0x00000008
    pcmfraction = 0x00000010
    modorder = 0x00000100
    modrow = 0x00000200
    modpattern = 0x00000400
    buffered = 0x10000000


class DebugFlags:
    """
    level_none: Disable all messages.
    level_error: Enable only error messages.
    level_warning: Enable warning and error messages.
    level_log: Enable informational, warning and error messages (default).
    type_memory: Verbose logging for memory operations, only use this if you are debugging a memory related issue.
    type_file: Verbose logging for file access, only use this if you are debugging a file related issue.
    type_codec: Verbose logging for codec initialization, only use this if you are debugging a codec related issue.
    type_trace: Verbose logging for internal errors, use this for tracking the origin of error codes.
    display_timestamps: Display the time stamp of the log message in milliseconds.
    display_linenumbers: Display the source code file and line number for where the message originated.
    display_threads: Display the thread ID of the calling function that generated the message.
    """
    level_none = 0x00000000
    level_error = 0x00000001
    level_warning = 0x00000002
    level_log = 0x00000004
    type_memory = 0x00000100
    type_file = 0x00000200
    type_codec = 0x00000400
    type_trace = 0x00000800
    display_timestamps = 0x00010000
    display_linenumbers = 0x00020000
    display_threads = 0x00040000


class InitFlags:
    """
    normal: Initialize normally.
    stream_from_update: No stream thread is created internally. Streams are driven from System::update. Mainly used with non-realtime outputs.
    mix_from_update: Win/PS3/Xbox 360 Only - FMOD Mixer thread is woken up to do a mix when System::update is called rather than waking periodically on its own timer.
    _3d_righthanded: FMOD will treat +X as right, +Y as up and +Z as backwards (towards you).
    channel_lowpass: All FMOD_3D based voices will add a software lowpass filter effect into the DSP chain which is automatically used when Channel::set3DOcclusion is used or the geometry API. This also causes sounds to sound duller when the sound goes behind the listener, as a fake HRTF style effect. Use System::setAdvancedSettings to disable or adjust cutoff frequency for this feature.
    channel_distancefilter: All FMOD_3D based voices will add a software lowpass and highpass filter effect into the DSP chain which will act as a distance-automated bandpass filter. Use System::setAdvancedSettings to adjust the center frequency.
    profile_enable: Enable TCP/IP based host which allows FMOD Designer or FMOD Profiler to connect to it, and view memory, CPU and the DSP network graph in real-time.
    vol0_becomes_virtual: Any sounds that are 0 volume will go virtual and not be processed except for having their positions updated virtually. Use System::setAdvancedSettings to adjust what volume besides zero to switch to virtual at. 
    geometry_usecloset: With the geometry engine, only process the closest polygon rather than accumulating all polygons the sound to listener line intersects.
    prefer_dolby_downmix: When using FMOD_SPEAKERMODE_5POINT1 with a stereo output device, use the Dolby Pro Logic II downmix algorithm instead of the SRS Circle Surround algorithm. 
    thread_unsafe: Disables thread safety for API calls. Only use this if FMOD low level is being called from a single thread, and if Studio API is not being used!
    profile_meter_all: Slower, but adds level metering for every single DSP unit in the graph. Use DSP::setMeteringEnabled to turn meters off individually. 
    """
    normal = 0x00000000
    stream_from_update = 0x00000001
    mix_from_update = 0x00000002
    _3d_righthanded = 0x00000004
    channel_lowpass = 0x00000100
    channel_distancefilter = 0x00000200
    profile_enable = 0x00010000
    vol0_becomes_virtual = 0x00020000
    geometry_usecloset = 0x00040000
    prefer_dolby_downmix = 0x00080000
    thread_unsafe = 0x00100000
    profile_meter_all = 0x00200000


class Sound:

    def __init__(self, sound=None):
        if sound is None:
            sound = c_voidp()
        self._sound = sound
    
    def get_num_subsounds(self):
        num_subsounds = c_int()
        FMOD.FMOD_Sound_GetNumSubSounds(self._sound, num_subsounds)
        return num_subsounds.value
    
    def get_subsound(self, int):
        subsound = c_voidp()
        FMOD.FMOD_Sound_GetSubSound(self._sound, 0, byref(subsound))
        return Sound(subsound)
    
    def release(self):
        FMOD.FMOD_Sound_Release(self._sound)


class Channel:

    def __init__(self, channel=None):
        if channel is None:
            channel = c_voidp()
        self._channel = channel
    
    def set_loop_count(self, loopcount: int=-1):
        FMOD.FMOD_Channel_SetLoopCount(self._channel, loopcount)
    
    def set_loop_points(self, loopstart: int, loopstarttype, loopend: int, loopendtype):
        FMOD.FMOD_Channel_SetLoopPoints(self._channel, loopstart, loopstarttype, loopend, loopendtype)
    
    def set_position(self, position: int, postype):
        FMOD.FMOD_Channel_SetPosition(self._channel, position, postype)
    
    def set_volume(self, volume: float=1.0):
        FMOD.FMOD_Channel_SetVolume(self._channel, c_float(volume))
    
    def stop(self):
        FMOD.FMOD_Channel_Stop(self._channel)


class System:

    def __init__(self, maxchannels: int, flags):
        self._system = c_voidp()
        FMOD.FMOD_System_Create(byref(self._system))
        FMOD.FMOD_System_Init(self._system, maxchannels, flags, 0)
    
    def create_stream(self, name_or_data: str, mode=0):
        sound = c_voidp()
        FMOD.FMOD_System_CreateStream(self._system, name_or_data.encode('ascii'), mode, 0, byref(sound))
        return Sound(sound)
    
    def play_sound(self, sound: Sound, channelgroup=0, paused: bool=False, channel: Channel=0):
        if isinstance(channelgroup, int) and isinstance(channel, int):
            FMOD.FMOD_System_PlaySound(self._system, sound._sound, 0, paused, 0)
        elif isinstance(channelgroup, int):
            FMOD.FMOD_System_PlaySound(self._system, sound._sound, 0, paused, byref(channel._channel))
        elif isinstance(channel, int):
            FMOD.FMOD_System_PlaySound(self._system, sound._sound, channelgroup._channelgroup, paused, 0)
        else:
            FMOD.FMOD_System_PlaySound(self._system, sound._sound, channelgroup._channelgroup, paused, byref(channel._channel))
    
    def release(self):
        FMOD.FMOD_System_Release(self._system)
    
    def update(self):
        FMOD.FMOD_System_Update(self._system)