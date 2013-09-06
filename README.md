# meldanya-backup

This is a simple backup script I wrote in Python once I realised my
server lacked backups and the hard drive was beginning to fail. It's
written in Python and uses the Dropbox and Google Drive Python SDKs in
order to backup stuff to these services. It's written to be easy to add
more storage providers (e.g. Box.net) in the future.

It's written with the intention of being run by e.g. cron or launchd. It
is not a fancy script which only backs up diffs and stuff. I wanted it
as easy as possible (and was in a bit of a hurry to get it done) and to
be able to use standard *NIX tools to restore (which means that there
is no restore functionality in the script).

The script will tar, compress and encrypt (with openssl) the
files/folders that are listed in the config file and upload them to
(currently) Dropbox or Google Drive. It behaves a bit different in the
different providers:

* In Dropbox, it gets it's own app folder (probably in
  Apps/meldanya-backup or whatever you named your Dropbox app).
* Int Google Drive, it will create a folder called meldanya_backup in
  the root of your Drive.

In both providers, it will create a new folder with the date and time of
the backup as the name. By default, it keeps the five latest backups to
save space.

## Dependencies

The script should be able to run on any Python 2.7 install with the
[Dropbox Python SDK](https://www.dropbox.com/developers/core/sdks/python)
and the [Google Drive Python SDK](https://developers.google.com/api-client-library/python/start/installation)
installed.

You also need to create applications on both [Dropbox](https://www.dropbox.com/developers/apps)
and [Google Drive](https://developers.google.com/api-client-library/python/start/get_started#setup).
Remember to keep the App key and secret from Dropbox and the Client ID
and secret from Google Drive. These should be entered into the config
file (described under Usage).

# Usage

	``` bash
	$ ./backup.py --help
	usage: backup.py [-h] [--loglevel LOGLEVEL] [--logfile LOGFILE]
					 [--config CONFIG]

	backup script

	optional arguments:
	  -h, --help           show this help message and exit
	  --loglevel LOGLEVEL  set the log level (NONE, DEBUG, INFO, WARNING or ERROR)
						   (default: ERROR)
	  --logfile LOGFILE    set the log file (absolute path) (default:
						   ~/.meldanya_backup.log)
	  --config CONFIG      set the config file (absolute path) (default:
						   ~/.meldanya_backup.conf)
	```

The script is configured through a config file written in JSON. There's
a sample config file in the project which you can use as a base. The
sample looks something like:

	```
	{
		"encrypt_pass": "/path/to/file/with/encryption/password",
		"providers" : {
			"google" : {
				"files": [
						"/path/to/dir/to/backup",
						"/path/to/another/dir"
				],
				"client_id" : "",
				"client_secret" : ""
			},
			"dropbox" : {
				"files": [
						"/path/to/file/to/backup/database.sql.gz"
				],
				"app_key" : "",
				"app_secret" : ""
			}
		}
	}
	```

Explanation of the options:

* `encrypt_pass` is used to specify the path to a file with a single
  line containing the encryption password (make sure NO ONE but you
  have read access to that file).
* `providers` is a dict of the providers to use.
* `<provider name>` is a dict of settings specific for that
  provider.
* `files` is an array of files to backup, this entry must reside
  inside a `<provider name>` and specifies which files to backup to that
  provider.
* `app_key`/`app_secret` is where you should enter the key and secret
  you got when registering your app with Dropbox.
* `client_id`/`client_secret` is where you should enter the id and
  secret when registering your app with Google Drive.

On the first run, you will have to go through an OAuth dance (all
providers will display an authentication URL which you will need to go
to, from these you will get the key that you should enter into the
program) to authenticate your newly created apps. After this run, the
backup script should be able to run by itself. It's probably a good idea
to run it manually the first time to make sure that it's working as it
should.


### Caveat

This might not be necessary to point out but I will do it anyways: **The
script MUST have read access to the files it is going to backup!**

## Common Problems

### Failed to parse config file: No JSON object could be decoded.
This error is when there's an error in the JSON syntax in the config
file, e.g. there's a comma to much (or to little). Python is fairly
nitpicky here so be sure to look over the syntax exactly.


## TODO
* Find out if [pycrypto](https://pypi.python.org/pypi/pycrypto) is
  faster than calling openssl and use it if it's faster.
* Add some sort of restore functionality (perhaps just download and
  decrypt the latest backup files at first).

