# Fairy Tale Playlist Picker

## Using the device

- **Turn the knob** to browse playlists. The screen shows each playlist's cover image and name.
- **Press the knob** to play the selected playlist on the speaker.
- After 60 seconds of no interaction, the screen turns off. Music continues playing.
- Any knob turn or press wakes the screen back up.
- When a playlist finishes, playback stops automatically. Nothing else plays.

## Managing playlists

### Add a playlist

1. SSH into the Pi: `ssh fairy@fairy.local`
2. List all your playlists to find the URI:
   ```
   cd ~/fairy
   source ~/fairy-env/bin/activate
   python list_playlists.py
   ```
3. Copy the URI (e.g., `spotify:playlist:xxxxx`) and add it to `config.py`:
   ```python
   PLAYLISTS = [
       "spotify:playlist:xxxxx",
       "spotify:playlist:yyyyy",  # new one
   ]
   ```
4. Delete the cache so images are re-fetched: `rm -rf cache/`
5. Restart the service: `sudo systemctl restart fairy`

### Remove a playlist

1. Remove the URI from `config.py`.
2. Restart the service: `sudo systemctl restart fairy`

## Changing the speaker

1. Make sure the speaker is active in Spotify (play something on it briefly).
2. Run `python tests/test_spotify.py` to see available devices and their IDs.
3. Update `SPOTIFY_DEVICE_ID` in `config.py`.
4. Restart the service: `sudo systemctl restart fairy`

## Re-authenticating Spotify

The Spotify token refreshes automatically. If it stops working:

1. On your laptop (not the Pi), from the `fairy` directory:
   ```
   python tests/spotify_auth.py
   ```
2. Log in when the browser opens.
3. Copy the token to the Pi:
   ```
   scp .spotify_cache fairy@fairy.local:~/fairy/.spotify_cache
   ```
4. Restart the service: `sudo systemctl restart fairy`

## Troubleshooting

### Check WiFi
```
ssh fairy@fairy.local
cd ~/fairy
source ~/fairy-env/bin/activate
python tests/test_wifi.py
```

### Run hardware diagnostics
```
python tests/test_all.py
```

### Check service logs
```
journalctl -u fairy -f
```

## Service management

| Action | Command |
|--------|---------|
| Start | `sudo systemctl start fairy` |
| Stop | `sudo systemctl stop fairy` |
| Restart | `sudo systemctl restart fairy` |
| Status | `sudo systemctl status fairy` |
| Live logs | `journalctl -u fairy -f` |
| Enable auto-start | `sudo systemctl enable fairy` |
| Disable auto-start | `sudo systemctl disable fairy` |

## Installing the service

Copy the service file and enable it:
```
sudo cp ~/fairy/fairy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fairy
sudo systemctl start fairy
```

## Updating the software

```
cd ~/fairy
git pull
sudo systemctl restart fairy
```

If dependencies changed:
```
source ~/fairy-env/bin/activate
pip install -r requirements.txt
sudo systemctl restart fairy
```
