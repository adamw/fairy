# Fairy Tale Playlist Picker

## Using the device

- **Turn the knob** to browse playlists. The screen shows each playlist's cover image and name.
- **Press the knob** to play the selected playlist on the speaker.
- After 60 seconds of no interaction, the screen turns off. Music continues playing.
- Any knob turn or press wakes the screen back up.
- When a playlist finishes, playback stops automatically. Nothing else plays.

## Managing playlists

Playlists are stored in a GitHub Gist (one Spotify URI per line). The device fetches the list on startup and refreshes it hourly.

### Add or remove a playlist

1. Find the URI: run `python list_playlists.py` to list your playlists.
2. Edit your gist — add or remove URIs (lines starting with `#` are ignored).
3. The device picks up changes automatically within an hour, or restart to apply immediately: `sudo systemctl restart fairy`

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

### Disable WiFi power saving

To prevent the Pi from becoming unreachable over WiFi:
```
sudo iw wlan0 set power_save off
```

Make it persistent by adding to `/etc/rc.local` (before `exit 0`):
```
iw wlan0 set power_save off
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

In one command:
```
git pull && sudo systemctl restart fairy && journalctl -u fairy -f
```