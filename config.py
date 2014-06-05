import ConfigParser

options = dict()

config = ConfigParser.RawConfigParser()
config.set("DEFAULT", "plugin_dir", "plugins")
config.set("DEFAULT", "progress_precision", "25")

config.add_section("logging")
config.set("logging", "file", "log.txt") #which file to log to
config.set("logging", "console", "False") #log to the console or not
config.set("logging", "log_sync", "False") #log information about sync packets
config.set("logging", "log_points", "False") # log every data point
config.set("logging", "log_stream", "False") # log every stream packet
config.set("logging", "log_control", "False") # log every control packet
config.set("logging", "log_msg", "False") # log all messages back and forth. (not streams)
config.set("logging", "log_buffer", "False") # log the entire buffer anytime there is at least one packet
config.set("logging", "log_parsing", "False") # log the parsing process
config.set("logging", "log_bad_checksum", "False") # log all bad checksums
config.set("logging", "debug_points", "False") # add debug information about points (for graph tools/recordings)
config.set("logging", "debug_dialog", "False") # Show dialog on debug packet

config.add_section("com")
config.set("com", "baud", "115200") #baud rate
config.set("com", "timeout", ".5") # timeout for initial port communication test
config.set("com", "thread_sleep", ".1") # ??
config.set("com", "flush", "1") # ??
config.set("com", "ignore_checksum", "False") # Ignore bad checksums
config.set("com", "buffer_size", "500") # buffer size for each channel

config.read("config.txt")


def load(section):
	for (k,v) in config.items(section):
		try:
			v = float(v)
			options[k] = v
		except ValueError:
			if v.lower() == "true":
				v = True
			elif v.lower() == "false":
				v = False
			options[k] = v

load("DEFAULT")
load("logging")
load("com")
