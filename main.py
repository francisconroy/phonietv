import time


def main():
    print("Hello from phonietv!")
    import vlc
    player = vlc.MediaPlayer('file:///home/francis/Downloads/Wall-E.avi')
    player.set_fullscreen(True)
    player.play()
    player.get_time()
    state = player.get_state()

    time.sleep(10)
    player.set_fullscreen(False)
    player.stop()
    # returns the corresponding instance
    pass


if __name__ == "__main__":
    main()
