# This file contains the media player functions
import time
import vlc

def on_finished(event):
    pass
    print("Media finished playing.")

if __name__ == "__main__":
    player = vlc.MediaPlayer(r'C:\Users\Francis\Downloads\sample-mp4-15s-11638kb.mp4')
    events = player.event_manager()
    events.event_attach(vlc.EventType.MediaP layerEndReached, on_finished)
    player.set_fullscreen(True)
    player.play()
    player.get_time()
    state = player.get_state()

    time.sleep(30)
    player.set_fullscreen(False)
    player.stop()
    # returns the corresponding instance
    pass