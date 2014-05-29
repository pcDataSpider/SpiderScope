import threading
import time

# class Thread.Timer A timer that repeats after the timer expires.
class Timer(threading.Thread):
	#constructor Timer(Float interval, Bool check, Function callable, [Value] args, {String:Value} kwargs) Construct a new repeateing Timer with the given parameters
	# interval = Time in seconds between triggers
	# check = 
	# callable = Function to be called when the timer expires
	# args = arguments passed to the callable function
	# kwargs = dictionary of keyword arguments passed to the callable function
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

    #function Timer.cancel() Cancels the timer and stops any pending actions.
    def cancel(self):
        self.event.clear()
	if self.t is not None:
		self.t.cancel()
