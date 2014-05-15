import threading
import time

 # --- Timer class that repeats after timer finishes.  ---
class Timer(threading.Thread):
    def __init__(self, interval, check, callable, *args, **kwargs):
        threading.Thread.__init__(self)
        self.interval = interval
	self.check = check
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.event = threading.Event()
        self.event.set()
	self.t = None
	self.daemon = True
	self.setDaemon(True)

    def run(self):
	self.nextevt = time.time()
        while self.event.is_set():
	    if self.check:
		    self.nextevt = self.nextevt + self.interval
		    self.nextint = self.nextevt - time.time() 
		    self.t = threading.Timer(self.nextint, self.callable,
                                self.args, self.kwargs)
            else:
		    self.t = threading.Timer(self.interval, self.callable,
                                self.args, self.kwargs)
            self.t.start()
            self.t.join()

    def cancel(self):
        self.event.clear()
	if self.t is not None:
		self.t.cancel()
