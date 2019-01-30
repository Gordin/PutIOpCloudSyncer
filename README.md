# PutIOpCloudSyncer
A simple application that moves stuff from put.io to pCloud

I'm playing around with multiprocessing here to have one download queue and one upload queue that don't have to wait for each other.

# Usage
- Fill in pCloud and put.io credentials (Get an OAUTH token with the AuthHelper)
- ./syncer.py list
- ./syncer.py filter 'START OF SOMETHING FROM ./syncer.py list'
(This is just to check that syncer.py chooses the right files)
- ./syncer.py sync 'START OF SOMETHING FROM ./syncer.py list' 'PATH ON PCLOUD'
