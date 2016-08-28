from fmod import System, Sound, Channel, Mode, TimeUnit, PluginType


class PlayAudio:
    """High level audio interface for fmod
    
    Attributes:
        flags (Mode.loop_normal|Mode.ignoretags): The flags for the system and sounds initializations.
        system: The system used by the interface.
        channel: The channel used by the system of the interface.
        sound: The current playing sound of the channel.
        repeat (False): Repeat the current playing sound.
        volume (1.0): A floating point number between 0 and 1 representing the volume.

    """

    def __init__(self, volume=1.0, repeat=False, flags=Mode.loop_normal|Mode.ignoretags):
        self.flags = flags
        self.system = System(1, self.flags)
        self.channel = Channel()
        self.sound = None
        self.set_volume(volume)
        self.set_repeat(repeat)
    
    def play_sound(self, path: str):
        """Plays an audio file.

        Args:
            path: The path of the audio file to play.
        
        """
        if self.sound is not None:
            # we free the last playing sound memory
            self.sound.release()
            del self.sound
        self.sound = self.system.create_stream(path, mode=self.flags)
        if self.sound.get_num_subsounds():
            self.sound = self.sound.get_subsound(0)
        self.set_repeat(self.repeat)
        self.system.play_sound(self.sound, channel=self.channel)
        self.channel.set_volume(self.volume)
    
    def get_position(self, time_unit: TimeUnit=TimeUnit.ms):
        """
        Args:
            time_unit (ms): The time unit used for the position.

        Returns:
            The current playback position for the specified channel.
        
        """
        return self.channel.get_position(time_unit)
    
    def is_playing(self) -> bool:
        """Retrieves the playing state.

        Returns:
            True if the channel of the interface is currently playing a sound, False otherwise.
        
        """
        return self.channel.is_playing()
    
    def set_paused(self, paused: bool):
        self.channel.set_paused(paused)
    
    def set_position(self, position: int, time_unit: TimeUnit=TimeUnit.ms):
        self.channel.set_position(position, time_unit)
    
    def set_repeat(self, repeat: bool=True):
        """Repeat the sound when after it ends

        Args:
            repeat (True): Enables or disables the looping of the track.
        
        """
        self.repeat = repeat
        self.channel.set_loop_count(-1 if repeat else 0)
        if self.sound is not None:
            self.sound.set_loop_count(-1 if repeat else 0)
    
    def set_volume(self, volume: float=1.0):
        self.volume = volume
        self.channel.set_volume(volume)
        
    def stop(self):
        if self.sound is not None:
            # we free the last playing sound memory
            self.sound.release()
            del self.sound
            self.sound = None
        self.channel.stop()