# xd_likes
There are two scripts: `likelog.py` for retrieving the likes section from X.com (Twitter), and `xd.py` for saving images from user IDs.

## likelog.py
This script retrieves the likes section and writes it to a log file.
In this case,
```
nohup ./likelog.py &
```
It is recommended to run it in the background.
(Unless you're very free, of course.)

I prefer to keep the log files as they are and do not perform any formatting at this stage. When using the log file in `xd.py` later, please output it like this:
```
cat .*.log | grep -oP "X id: .*," | grep -oP "\".*\"" | sed -z  "s/\n/ ,/g"
```

## xd.py
This script saves images.
Please put the values obtained from `grep` into `USER_SCREEN_NAMES`.
Then just run it:
```
nohup ./xd.py &
```
