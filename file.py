from time import sleep
import json
import paho.mqtt.client as mqtt
import pyaudio
import sys
import numpy as np
import aubio
import aiohttp
import asyncio


# Set up MQTT client
client = mqtt.Client()
client.connect("192.168.100.250", 1883)

topic = "cmnd/officelamp/Color2"
topic2 = "cmnd/tvlamp2/Color2"

colour1 = "255,0,0"
colour2 = "0,255,0"
colour3 = "0,0,255"

last_value = colour1

colour_values = [
[50,'174,0,0'],
[59,'255,0,0'],
[68,'255,0,0'],
[77,'255,102,0'],
[86,'255,239,0'],
[95,'153,255,0'],
[104,'40,255,0'],
[113,'0,255,242'],
[122,'0,122,255'],
[131,'5,0,255'],
[140,'71,0,237'],
[149,'99,0,178'],
[158,'174,0,0'],
[167,'255,0,0'],
[176,'255,0,0'],
[185,'255,102,0'],
[194,'255,239,0'],
[203,'153,255,0'],
[212,'40,255,0'],
[221,'0,255,242'],
[230,'0,122,255'],
[239,'5,0,255'],
[248,'71,0,237'],
[257,'99,0,178'],
[266,'174,0,0'],
[275,'255,0,0'],
[284,'255,0,0'],
[293,'255,102,0'],
[302,'255,239,0'],
[311,'153,255,0'],
[320,'40,255,0'],
[329,'0,255,242'],
[338,'0,122,255'],
[347,'5,0,255'],
[356,'71,0,237'],
[365,'99,0,178'],
[374,'174,0,0'],
[383,'255,0,0'],
[392,'255,0,0'],
[401,'255,102,0'],
[410,'255,239,0'],
[419,'153,255,0'],
[428,'40,255,0'],
[437,'0,255,242'],
[446,'0,122,255'],
[455,'5,0,255'],
[464,'71,0,237'],
[473,'99,0,178'],
]

# def ranges(value):
#     for i  in array:
#         if value < i:
#             print (i)
#             break

# ranges(24)
# quit()

def change_colour(value):
    # for i in colour_values:
    #     if value < i[0]:
    #         # print (i[1])
    #         return i[1]
    one= np.random.randint(0,255)
    two= np.random.randint(0,255)
    three= np.random.randint(0,255)
    return (f"{one},{two},{three}")

    # one= "255,0,0"
    # two= "0,255,0"
    # three= "0,0,255"
    # l = np.random.randint(0,3)
    # if l == 0:
    #     return one
    # elif l == 1:
    #     return two
    # elif l == 2:
    #     return three

# initialise pyaudio
p = pyaudio.PyAudio()

# open stream
buffer_size = 512
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=samplerate,
                input=True,
                frames_per_buffer=buffer_size)

# setup pitch
tolerance = 0.8
win_s = 1024 # fft size
hop_s =  buffer_size # hop size
a_tempo = aubio.tempo("default", win_s, hop_s, samplerate)
a_pitch = aubio.pitch("default", win_s, hop_s, samplerate)
a_pitch.set_unit("Hz")
a_pitch.set_tolerance(tolerance)

print("*** starting recording")

while True:
    try:
        audiobuffer = stream.read(buffer_size)
        signal = np.fromstring(audiobuffer, dtype=np.float32)
        is_beat = a_tempo(signal)
        # print(a_pitch(signal))
        pitch = a_pitch(signal)[0]
        if is_beat and pitch > 0:
            print(pitch)
            colour = change_colour(pitch)
            client.publish("zigbee2mqtt/LED Strip/set", json.dumps({"state" : "ON", "transition": 0.001, "color":{"rgb": colour}}))
            client.publish(topic, colour)

    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

print("*** done recording")
stream.stop_stream()
stream.close()
p.terminate()