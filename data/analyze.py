"""
This Python 3 file will read a noisy ECG signal from ecg.wav
reduce the noise using FFT/iFFT low-pass filtering, then
plot the result interactively.
"""

import wave
import numpy as np
import matplotlib.pyplot as plt


def lowpassFFT(signal, rate, cutoff):
    """Lowpass a signal using FFT/iFFT"""
    fft = np.fft.fft(signal)
    fftfreq = np.fft.fftfreq(len(signal), 1/rate)
    for i, freq in enumerate(fftfreq):
        if abs(freq) >= cutoff:
            fft[i] = 0
    signal = np.fft.ifft(fft)
    return signal


if __name__ == "__main__":

    # Load ECG data from the WAV file
    wf = wave.open("ecg.wav")
    RATE = 1000
    assert wf.getnchannels != 2, "WAV must be mono"
    PCM = np.fromstring(wf.readframes(-1), np.int16)

    # invert the PCM data (50% chance it's upside down)
    PCM *= -1

    # create a time series to match the PCM series
    Xs = np.arange(len(PCM))/RATE
    Ys = lowpassFFT(PCM, RATE, 60/2)

    # plot the data
    plt.figure(figsize=(8, 3))
    plt.plot(Xs, PCM, lw=.5, color='.8', label="original")
    plt.plot(Xs, Ys, color='b', alpha=.5, label="filtered")
    plt.axis([5.3, 8.5, None, None])

    # style the plot
    plt.axis('off')
    plt.margins(0, .05)
    plt.tight_layout()
    plt.legend()
    plt.savefig("result2.png")
    plt.show()
