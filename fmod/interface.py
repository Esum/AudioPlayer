from fmod import System, Sound, Channel, TimeUnit


class PlayAudio:

    def __init__(self):
        self.system = System(1, 0)
        self.channel = Channel()
    
    def play_sound(self, path: str):
        sound = self.system.create_stream(path)
        if sound.get_num_subsounds():
            sound = souns.get_subsound(0)
        self.system.play_sound(sound, channel=self.channel)
    
    def set_position(self, position: int, time_unit: TimeUnit=TimeUnit.ms):
        self.channel.set_position(position, time_unit)
    
    def set_repeat(self, repeat: bool=True):
        self.channel.set_loop_count(-1 if repeat else 0)
    
    def set_volume(self, volume: float=1.0):
        self.channel.set_volume(volume)
        
    def stop(self):
        self.channel.stop()