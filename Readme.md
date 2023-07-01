# CFX Status Bot
* You need python installed

## Execute Bot
* pip install requests
* python status.py

## Config
Please do not add the Comments in the config.json or you will break the script
```json
{
  "token": "MTA1NTYxNzA4OTk1MzU5", // Bot Token
  "refresh_interval": 60, // Refresh interval in seconds
  "channel_id": 112468829, // Channel ID where the Message will be sent
  "edit_channel_name": true, // Set false if you don't want to edit the channel
  "channel_name": "cfx-status" // Channel name that will be set after starting the Bot
}
```