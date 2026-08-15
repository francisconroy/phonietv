# phonietv
Like the phoniebox but for TV (and audiobooks/music too).
## Current features
- Plays video files mp4, mkv, avi.
- Uses VLC media player for playback
- Supports Linux filesystem paths at present including mounted shares
- Can play a directory of media files or a single file per token (NFC tag)
- Supports NFC tags which contain a text string
- Supports play/resume of the same file
- Keeps track of the last played file when playing a directory of media files
- Has a working timer interface to limit screen time on a per day basis

## TODO
-[ ] Remove/override the default terminal window from the OS
- [ ] Add a web interface for configuration and control
- [ ] Finish adding the screen time timer interface (Blinkt LEDs)

# Design
The design for phonieTV is as follows:
- Based around a raspberryPI at least 3B+ for 1080p playback (H.264)
- Running standard Raspberry PI OS
- Connects to a TV using HDMI (optionally supporting HDMI-CEC)

Using a custom designed 3D printed enclosure to house the Raspberry PI, NFC HAT and Blinkt LED HAT. The enclosure will have a slot for the NFC tokens to be placed in front of the reader.
See the onShape design files: https://cad.onshape.com/documents/2257fa4e5b278c100cb08ead/w/fe4415ab1f41311456213ed2/e/246fcc7994ddedbc314a9c4c?renderMode=0&uiState=6a8033c12764a0ab4a81e978

## Interfaces
- HDMI CEC - For controlling TV power and input channel (TBD)
- Kid-friendly media selection interface (see dedicated section)
- LED indicator for screen time timer (Pimoroni Blinkt)

## Kid-friendly interface
The interface consists of:
- 3D printed enclosure for Raspberry PI + NFC HAT + Blinkt LED HAT

## Configuration
1. Configure your video source directory
2. Map NFC tokens (e.g. Bluey) to a subdirectory or individual video/audio files
3. Write token ID field on your NFC tokens


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