from ctypes import *


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


class Mode:
    """
    default: default for all modes listed below. loop_off, _2d, _3d_worldrelative, _3d_inverserolloff
    loop_off: For non looping sounds. (default). Overrides loop_normal / loop_bidi.
    loop_normal: For forward looping sounds.
    loop_bidi: For bidirectional looping sounds. (only works on software mixed static sounds).
    _2d: Ignores any 3d processing. (default).
    _3d: Makes the sound positionable in 3D. Overrides _2d.
    createstream: Decompress at runtime, streaming from the source provided (ie from disk). Overrides createsample and createcompressedsample. Note a stream can only be played once at a time due to a stream only having 1 stream buffer and file handle. Open multiple streams to have them play concurrently.
    createsample: Decompress at loadtime, decompressing or decoding whole file into memory as the target sample format (ie PCM). Fastest for playback and most flexible.
    createcompressedsample: Load MP2/MP3/IMAADPCM/Vorbis/AT9 or XMA into memory and leave it compressed. Vorbis/AT9 encoding only supported in the FSB file format. During playback the FMOD software mixer will decode it in realtime as a 'compressed sample'. Overrides REATESAMPLE. If the sound data is not one of the supported formats, it will behave as if it was created with FMOD_CREATESAMPLE and decode the sound into PCM.
    openuser: Opens a user created static sample or stream. Use FMOD_CREATESOUNDEXINFO to specify format and/or read callbacks. If a user created 'sample' is created with no read callback, the sample will be empty. Use Sound::lock and Sound::unlock to place sound data into the sound if this is the case.
    openmemory: "name_or_data" will be interpreted as a pointer to memory instead of filename for creating sounds. Use FMOD_CREATESOUNDEXINFO to specify length. If used with createsample or, createcompressedsample, FMOD duplicates the memory into its own buffers. Your own buffer can be freed after open. If used with createstream, FMOD will stream out of the buffer whose pointer you passed in. In this case, your own buffer should not be freed until you have finished with and released the stream.
    openmemory_point: "name_or_data" will be interpreted as a pointer to memory instead of filename for creating sounds. Use FMOD_CREATESOUNDEXINFO to specify length. This differs to openmemory in that it uses the memory as is, without duplicating the memory into its own buffers. Cannot be freed after open, only after Sound::release. Will not work if the data is compressed and FMOD_CREATECOMPRESSEDSAMPLE is not used.
    openraw: Will ignore file format and treat as raw pcm. Use FMOD_CREATESOUNDEXINFO to specify format. Requires at least defaultfrequency, numchannels and format to be specified before it will open. Must be little endian data.
    openonly: Just open the file, dont prebuffer or read. Good for fast opens for info, or when sound::readData is to be used.
    accuratetime: For System::createSound - for accurate Sound::getLength/Channel::setPosition on VBR MP3, and MOD/S3M/XM/IT/MIDI files. Scans file first, so takes longer to open. openonly does not affect this.
    mpegsearch: For corrupted / bad MP3 files. This will search all the way through the file until it hits a valid MPEG header. Normally only searches for 4k.
    nonblocking: For opening sounds and getting streamed subsounds (seeking) asyncronously. Use Sound::getOpenState to poll the state of the sound as it opens or retrieves the subsound in the background.
    unique: unique sound, can only be played one at a time.
    _3d_headrelative: Make the sound's position, velocity and orientation relative to the listener.
    _3d_worldrelative: Make the sound's position, velocity and orientation absolute (relative to the world). (default)
    _3d_inverserolloff: This sound will follow the inverse rolloff model where mindistance = full volume, maxdistance = where sound stops attenuating, and rolloff is fixed according to the global rolloff factor. (default)
    _3d_linearrolloff: This sound will follow a linear rolloff model where mindistance = full volume, maxdistance = silence.
    _3d_linearsquarerolloff: This sound will follow a linear-square rolloff model where mindistance = full volume, maxdistance = silence.
    _3d_inversetaperedrolloff: This sound will follow the inverse rolloff model at distances close to mindistance and a linear-square rolloff close to maxdistance.
    _3d_customrolloff: This sound will follow a rolloff model defined by Sound::set3DCustomRolloff / Channel::set3DCustomRolloff.
    _3d_ignoregeometry: Is not affect by geometry occlusion. If not specified in Sound::setMode, or Channel::setMode, the flag is cleared and it is affected by geometry again.
    ignoretags: Skips id3v2/asf/etc tag checks when opening a sound, to reduce seek/read overhead when opening files (helps with CD performance).
    lowmem: Removes some features from samples to give a lower memory overhead, like Sound::getName. See remarks.
    loadsecondaryram: Load sound into the secondary RAM of supported platform. On PS3, sounds will be loaded into RSX/VRAM.
    virtual_playfromstart: For sounds that start virtual (due to being quiet or low importance), instead of swapping back to audible, and playing at the correct offset according to time, this flag makes the sound play from the start.
    """
    default = 0x00000000
    loop_off = 0x00000001
    loop_normal = 0x00000002
    loop_bidi = 0x00000004
    _2d = 0x00000008
    _3d = 0x00000010
    createstream = 0x00000080
    createsample = 0x00000100
    createcompressedsample = 0x00000200
    openuser = 0x00000400
    openmemory = 0x00000800
    openmemory_point = 0x10000000
    openraw = 0x00001000
    openonly = 0x00002000
    accuratetime = 0x00004000
    mpegsearch = 0x00008000
    nonblocking = 0x00010000
    unique = 0x00020000
    _3d_headrelative = 0x00040000
    _3d_worldrelative = 0x00080000
    _3d_inverserolloff = 0x00100000
    _3d_linearrolloff = 0x00200000
    _3d_linearsquarerolloff = 0x00400000
    _3d_inversetaperedrolloff = 0x00800000
    _3d_customrolloff = 0x04000000
    _3d_ignoregeometry = 0x40000000
    ignoretags = 0x02000000
    lowmem = 0x08000000
    loadsecondaryram = 0x20000000
    virtual_playfromstart = 0x80000000


class Sound:
    """Sound object

    Attributes:
        _sound (c_voidp): A C pointer to the sound.
    
    """

    def __init__(self, sound=None):
        if sound is None:
            sound = c_voidp()
        self._sound = sound
    
    def get_loop_count(self):
        """Retrieves the current loop count value for the specified sound.

        Returns:
            The number of times a sound will loop by default before stopping. 0 = oneshot. 1 = loop once then stop. -1 = loop forever.
        
        Remarks:
            Unlike the channel loop count function, this function simply returns the value set with Sound::setLoopCount. It does not decrement as it plays (especially seeing as one sound can be played multiple times).
        
        """
        loopcount = c_int()
        FMOD.FMOD_Sound_GetNumSubSounds(self._sound, loopcount)
        return loopcount.value
    
    def get_num_subsounds(self):
        num_subsounds = c_int()
        FMOD.FMOD_Sound_GetNumSubSounds(self._sound, num_subsounds)
        return num_subsounds.value
    
    def get_subsound(self, numsubsound: int):
        subsound = c_voidp()
        FMOD.FMOD_Sound_GetSubSound(self._sound, numsubsound, byref(subsound))
        return Sound(subsound)
    
    def set_loop_count(self, loopcount: int=-1):
        """Sets a sound, by default, to loop a specified number of times before stopping if its mode is set to FMOD_LOOP_NORMAL or FMOD_LOOP_BIDI.

        Args:
            loopcount (-1): Number of times to loop before stopping. 0 = oneshot. 1 = loop once then stop. -1 = loop forever.
        
        """
        FMOD.FMOD_Sound_SetLoopCount(self._sound, loopcount)
    
    def release(self):
        """Frees a sound object.

        Remarks:
            This will free the sound object and everything created under it.
            If this is a stream that is playing as a subsound of another parent stream, then if this is the currently playing subsound, the whole stream will stop.
            Note - This function will block if it was opened with Mode.nonblocking and hasn't finished opening yet.
        
        """
        FMOD.FMOD_Sound_Release(self._sound)


class Channel:
    """Channel object

    Attributes:
        _channel (c_voidp): A C pointer to the channel.

    """

    def __init__(self, channel=None):
        if channel is None:
            channel = c_voidp()
        self._channel = channel
    
    def get_loop_count(self) -> int:
        loopcount = c_int()
        FMOD.FMOD_Channel_GetLoopCount(self._channel, byref(loopcount))
        return loopcount.value
    
    def get_paused(self) -> bool:
        """Retrieves the paused state.

        Returns:
            True if the current played sound is paused, False otherwise.
        
        """
        paused = c_bool()
        FMOD.FMOD_Channel_GetPaused(self._channel, byref(paused))
        return paused.value

    def get_position(self, postype) -> int:
        """
        Args:
            Time unit to retrieve into the position parameter. See TimeUnit.

        Returns:
            The current playback position for the specified channel.
        
        """
        position = c_uint()
        FMOD.FMOD_Channel_GetPosition(self._channel, byref(position), postype)
        return position.value
    
    def is_playing(self) -> bool:
        """Retrieves the playing state.

        Returns:
            True if the channel of the interface is currently playing a sound, False otherwise.
        
        """
        playing = c_bool()
        FMOD.FMOD_Channel_IsPlaying(self._channel, byref(playing))
        return playing.value
    
    def set_loop_count(self, loopcount: int=-1):
        FMOD.FMOD_Channel_SetLoopCount(self._channel, loopcount)
    
    def set_loop_points(self, loopstart: int, loopstarttype, loopend: int, loopendtype):
        FMOD.FMOD_Channel_SetLoopPoints(self._channel, loopstart, loopstarttype, loopend, loopendtype)
    
    def set_paused(self, paused: bool):
        FMOD.FMOD_Channel_SetPaused(self._channel, paused)
    
    def set_position(self, position: int, postype):
        FMOD.FMOD_Channel_SetPosition(self._channel, position, postype)
    
    def set_volume(self, volume: float=1.0):
        FMOD.FMOD_Channel_SetVolume(self._channel, c_float(volume))
    
    def stop(self):
        FMOD.FMOD_Channel_Stop(self._channel)


class System:
    """System object

    Attributes:
        _system (c_voidp): A C pointer to the system.
    
    """

    def __init__(self, maxchannels: int, flags):
        """Creates the system object and initializes it, and the sound device.

        Args:
            maxchannels: The maximum number of channels to be used in FMOD. They are also called 'virtual channels' as you can play as many of these as you want, even if you only have a small number of software voices. See remarks for more.
            flags: See InitFlags. This can be a selection of flags bitwise OR'ed together to change the behaviour of FMOD at initialization time.
        
        Remarks:
            Virtual channels.
            These types of voices are the ones you work with using the FMOD::Channel API. The advantage of virtual channels are, unlike older versions of FMOD, you can now play as many sounds as you like without fear of ever running out of voices, or playsound failing. You can also avoid 'channel stealing' if you specify enough virtual voices.
            As an example, you can play 1000 sounds at once, even on a 32 channel soundcard.
            FMOD will only play the most important/closest/loudest (determined by volume/distance/geometry and priority settings) voices, and the other 968 voices will be virtualized without expense to the CPU. The voice's cursor positions are updated.
            When the priority of sounds change or emulated sounds get louder than audible ones, they will swap the actual voice resource over and play the voice from its correct position in time as it should be heard.
            What this means is you can play all 1000 sounds, if they are scattered around the game world, and as you move around the world you will hear the closest or most important 32, and they will automatically swap in and out as you move.
            Currently the maximum channel limit is 4093.
        
        """
        self._system = c_voidp()
        FMOD.FMOD_System_Create(byref(self._system))
        FMOD.FMOD_System_Init(self._system, maxchannels, flags, 0)
    
    def create_stream(self, name_or_data: str, mode=0):
        """Opens a sound for streaming. This function is a helper function that is the same as System.create_sound but has the createstream flag added internally.

        Args:
            name_of_data (str): Name of the file or URL to open encoded in a UTF-8 string.
            mode: Behaviour modifier for opening the sound. See Mode. Also see remarks for more.

        Returns:
            A Sound object created from the name_of_data

        """
        sound = c_voidp()
        FMOD.FMOD_System_CreateStream(self._system, name_or_data.encode('ascii'), mode, 0, byref(sound))
        return Sound(sound)
    
    def play_sound(self, sound: Sound, channelgroup=0, paused: bool=False, channel: Channel=0):
        """Plays a sound object on a particular channel and ChannelGroup if desired.

        Args:
            sound: A sound to play.
            channelgroup: A channelgroup become a member of. This is more efficient than using Channel.set_channel_group, as it does it during the channel setup, rather than connecting to the master channel group, then later disconnecting and connecting to the new channelgroup when specified. Optional. Use 0/NULL to ignore (use master ChannelGroup).
            paused: True or false flag to specify whether to start the channel paused or not. Starting a channel paused allows the user to alter its attributes without it being audible, and unpausing with Channel::setPaused actually starts the sound.
            channel (0): A channel that receives the newly playing channel. Optional. Use 0 to ignore.
        
        """
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