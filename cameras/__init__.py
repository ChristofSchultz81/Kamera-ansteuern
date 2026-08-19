"""Package containing all camera driver implementations and the generic driver API.

Every camera model is represented by one driver class implementing
``CameraDriver`` (see base.py). New camera hardware only needs a new
driver module + a registry entry; the GUI code never needs to change.
"""
