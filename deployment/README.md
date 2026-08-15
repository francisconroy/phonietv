# Running phonieTV as a service
Install the service file to run phonieTV as a service on boot. This will allow the box to start up and run without needing to log in.

1. Copy the service file to the systemd directory:
```bash
sudo cp deployment/phonietv.service /etc/systemd/system/phonietv.service
sudo systemctl daemon-reload
sudo systemctl enable phonietv
sudo systemctl start phonietv
sudo systemctl status phonietv --no-pager
```