# CFX Status Bot
Python Bot that will show the current CFX Status

![Screenshot_213](https://github.com/Musiker15/CFX-Status-Bot-V2/assets/49867381/0c44b506-1874-4152-92f8-f3767faf9a64)

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
