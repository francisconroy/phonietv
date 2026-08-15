# phonietv
Like the phoniebox but for TV (and audiobooks/music too).


# Design
The design for phonieTV is as follows:
- Based around a raspberryPI at least 3B+ for 1080p playback
- Running standard Raspberry PI OS
- Connects to a TV using HDMI (optionally supporting HDMI-CEC)
## Interfaces
- HDMI CEC - For controlling TV power and input channel
- Kid-friendly media selection interface (see dedicated section)
- LED indicator for screen time timer (Pimoroni Blinkt)

## Kid-friendly interface
The interface consists of:
- 3D printed enclosure for Raspberry PI + NFC HAT + Blinkt LED HAT

## Configuration
1. Configure your video source directory
2. Map NFC tokens (e.g. Bluey) to a subdirectory or individual video/audio files
3. Write token ID field on your NFC tokens

### How it works
- There is a 


### Operation instructions:
1. Parent sets up PhonieTV by installing software and running it on the box
2. Parent places media into the media directory
3. Parent populates media_layout.toml with details about how each directory is organised and importantly which card ID


# Future ideas
- Build a parent web interface
  - Including parental controls (rating)
  - Screen time limiter
  - Remote lock
  - Volume control
  - Subtitle control
  - Manual video selection
- Streaming support 
  - Youtube
  - Netflix
- Support custom playlists, map a custom list of items to a token


### Mounting a CIFS (Samba) share in Raspberry PI OS
1. Install cifs-utils if not already installed
1. Set up mount point `sudo mkdir -p /mnt/video`
2. Add line to FStab `sudo echo "//franksdisko.local/movies  /mnt/video  cifs  guest,uid=1000,gid=1000,iocharset=utf8,_netdev,x-systemd.automount,nofail  0  0" >> /etc/fstab`
  This version of the line is for a guest share, if you have a username/password protected share you'll have to create a credentials file and use that instead of `guest` in the fstab line.
  For simplicity, I recommend creating a readonly guest user on your NAS for the phonieTV box to use.
3. Reload systemd-daemon `sudo systemctl daemon-reload`
4. Apply the mounts `sudo mount -a`