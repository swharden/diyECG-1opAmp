"""
The core SWHEar class for continuously monitoring microphone data.

The Ear class is the primary method used to access microphone data.
It has extra routines to audomatically detec/test sound card, channel,
and rate combinations to maximize likelyhood of finding one that
works on your system (all without requiring user input!)

Although this was designed to be a package, it's easy enough to work
as an entirely standalone python script. Just drop this .py file in
your project and import it by its filename. Done!
"""

import pyaudio
import time
import numpy as np
import threading
import scipy.io.wavfile

def FFT(data,rate):
    """given some data points and a rate, return [freq,power]"""
    data=data*np.hamming(len(data))
    fft=np.fft.fft(data)
    fft=10*np.log10(np.abs(fft))
    freq=np.fft.fftfreq(len(fft),1/rate)
    return freq[:int(len(freq)/2)],fft[:int(len(fft)/2)]

class Ear(object):
    def __init__(self,device=None,rate=None,chunk=4096,maxMemorySec=5):
        """
        Prime the Ear class to access audio data. Recording won't start
        until stream_start() is called.
        - if device is none, will use first valid input (not system default)
        - if a rate isn't specified, the lowest usable rate will be used.
        """

        # configuration
        self.chunk = chunk # doesn't have to be a power of 2
        self.maxMemorySec = maxMemorySec # delete if more than this around
        self.device=device
        self.rate=rate

        # internal variables
        self.chunksRecorded=0
        self.p=pyaudio.PyAudio() #keep this forever
        self.t=False #later will become threads

    ### SOUND CARD TESTING

    def valid_low_rate(self,device):
        """set the rate to the lowest supported audio rate."""
        for testrate in [8000, 9600, 11025, 12000, 16000, 22050, 24000,
                         32000, 44100, 48000, 88200, 96000, 192000]:
            if self.valid_test(device,testrate):
                return testrate
        print("SOMETHING'S WRONG! I can't figure out how to use DEV",device)
        return None

    def valid_test(self,device,rate=44100):
        """given a device ID and a rate, return TRUE/False if it's valid."""
        try:
            self.info=self.p.get_device_info_by_index(device)
            if not self.info["maxInputChannels"]>0:
                return False
            stream=self.p.open(format=pyaudio.paInt16,channels=1,
               input_device_index=device,frames_per_buffer=self.chunk,
               rate=int(self.info["defaultSampleRate"]),input=True)
            stream.close()
            return True
        except:
            return False

    def valid_input_devices(self):
        """
        See which devices can be opened for microphone input.
        call this when no PyAudio object is loaded.
        """
        mics=[]
        for device in range(self.p.get_device_count()):
            if self.valid_test(device):
                mics.append(device)
        if len(mics)==0:
            print("no microphone devices found!")
        else:
            print("found %d microphone devices: %s"%(len(mics),mics))
        return mics

    ### SETUP AND SHUTDOWN

    def initiate(self):
        """
        run this after changing settings (like rate) before recording.
        mostly just ensures the sound card settings are good.
        """
        if self.device is None:
            self.device=self.valid_input_devices()[0] #pick the first one
        if self.rate is None:
            self.rate=self.valid_low_rate(self.device)
        if not self.valid_test(self.device,self.rate):
            print("guessing a valid microphone device/rate...")
            self.device=self.valid_input_devices()[0] #pick the first one
            self.rate=self.valid_low_rate(self.device)
        self.msg='recording from "%s" '%self.info["name"]
        self.msg+='(device %d) '%self.device
        self.msg+='at %d Hz'%self.rate
        self.data=np.array([])
        print(self.msg)


    def close(self):
        """gently detach from things."""
        print(" -- sending stream termination command...")
        self.keepRecording=False #the threads should self-close
        if self.t:
            while(self.t.isAlive()):
                time.sleep(.1) #wait for all threads to close
            self.stream.stop_stream()
        self.p.terminate()

    ### LIVE AUDIO STREAM HANDLING

    def stream_readchunk(self):
        """reads some audio and re-launches itself"""
        try:
            data = np.fromstring(self.stream.read(self.chunk),dtype=np.int16)
            self.data=np.concatenate((self.data,data))
            self.chunksRecorded+=1
            self.dataFirstI=self.chunksRecorded*self.chunk-len(self.data)
            if len(self.data)>self.maxMemorySec*self.rate:
                pDump=len(self.data)-self.maxMemorySec*self.rate
                #print(" -- too much data in memory! dumping %d points."%pDump)
                self.data=self.data[pDump:]
                self.dataFirstI+=pDump
        except Exception as E:
            print(" -- exception! terminating...")
            print(E,"\n"*5)
            self.keepRecording=False
        if self.keepRecording==True:
            self.stream_thread_new()
        else:
            self.stream.close()
            self.p.terminate()
            self.keepRecording=None
            print(" -- stream STOPPED")

    def stream_thread_new(self):
        self.t=threading.Thread(target=self.stream_readchunk)
        self.t.start()

    def stream_start(self):
        """adds data to self.data until termination signal"""
        self.initiate()
        print(" -- starting stream")
        self.keepRecording=True # set this to False later to terminate stream
        self.dataFiltered=None #same
        self.stream=self.p.open(format=pyaudio.paInt16,channels=1,
                      rate=self.rate,input=True,frames_per_buffer=self.chunk)
        self.stream_thread_new()

    def stream_stop(self,waitForIt=True):
        """send the termination command and (optionally) hang till its done"""
        self.keepRecording=False
        if waitForIt==False:
            return
        while self.keepRecording is False:
            time.sleep(.1)

    ### WAV FILE AUDIO

    def loadWAV(self,fname):
        """Add audio into the buffer (self.data) from a WAV file"""
        self.rate,self.data=scipy.io.wavfile.read(fname)
        print("loaded %.02f sec of data (rate=%dHz)"%(len(self.data)/self.rate,
                                                     self.rate))
        self.initiate()
        return

    ### DATA RETRIEVAL
    def getPCMandFFT(self):
        """returns [data,fft,sec,hz] from current memory buffer."""
        if not len(self.data):
            return
        data=np.array(self.data) # make a copy in case processing is slow
        sec=np.arange(len(data))/self.rate
        hz,fft=FFT(data,self.rate)
        return data,fft,sec,hz

    def softEdges(self,data,fracEdge=.05):
        """multiple edges by a ramp of a certain percentage."""
        rampSize=int(len(data)*fracEdge)
        mult = np.ones(len(data))
        window=np.hanning(rampSize*2)
        mult[:rampSize]=window[:rampSize]
        mult[-rampSize:]=window[-rampSize:]
        return data*mult

    def getFiltered(self,freqHighCutoff=50):
        if freqHighCutoff<=0:
            return self.data
        fft=np.fft.fft(self.softEdges(self.data)) #todo: filter needed?
        trim=len(fft)/self.rate*freqHighCutoff
        fft[int(trim):-int(trim)]=0
        return np.real(np.fft.ifft(fft))


if __name__=="__main__":
    print("This script is intended to be imported, not run directly!")
