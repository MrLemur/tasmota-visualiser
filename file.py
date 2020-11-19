from time import sleep
import json
import paho.mqtt.client as mqtt
import pyaudio
import sys
import numpy as np
import aubio
import aiohttp
import asyncio
from random import randint


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
    {"colour": "dark red", "value": "174,0,0"},
    {"colour": "red", "value": "255,0,0"},
    {"colour": "orange-red", "value": "255,102,0"},
    {"colour": "yellow", "value": "255,239,0"},
    {"colour": "chartreuse", "value": "153,255,0"},
    {"colour": "lime", "value": "40,255,0"},
    {"colour": "aqua", "value": "0,255,242"},
    {"colour": "sky blue", "value": "0,122,255"},
    {"colour": "blue", "value": "5,0,255"},
    {"colour": "blue", "value": "71,0,237"},
    {"colour": "indigo", "value": "99,0,178"},
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
    # one= np.random.randint(0,255)
    # two= np.random.randint(0,255)
    # three= np.random.randint(0,255)
    number = randint(0, len(colour_values) - 1)
    return colour_values[number]
    # return (f"{one},{two},{three}")

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
stream = p.open(
    format=pyaudio_format,
    channels=n_channels,
    rate=samplerate,
    input=True,
    frames_per_buffer=buffer_size,
)

# setup pitch
tolerance = 0.8
win_s = 1024  # fft size
hop_s = buffer_size  # hop size
a_tempo = aubio.tempo("default", win_s, hop_s, samplerate)
a_pitch = aubio.pitch("default", win_s, hop_s, samplerate)
a_pitch.set_unit("Hz")
a_pitch.set_tolerance(tolerance)

print("*** starting recording")

last_colour = ""
while True:
    try:
        audiobuffer = stream.read(buffer_size)
        signal = np.fromstring(audiobuffer, dtype=np.float32)
        is_beat = a_tempo(signal)
        # print(a_pitch(signal))
        pitch = a_pitch(signal)[0]
        if is_beat[0]:
            print(pitch)
            colour_dict = change_colour(pitch)
            while colour_dict["value"] == last_colour:
                colour_dict = change_colour(pitch)
            print(f"Setting colour to {colour_dict['colour']}")
            client.publish(
                "zigbee2mqtt/LED Strip/set",
                json.dumps(
                    {
                        "state": "ON",
                        "brightness": 255,
                        "transition": 0.001,
                        "color": {"rgb": colour_dict["value"]},
                    }
                ),
            )
            client.publish(topic, colour_dict["value"])
            # client.publish("cmnd/tvlamp/Color2", colour_dict["value"])
            # client.publish("cmnd/tvlamp2/Color2", colour_dict["value"])
            last_colour = colour_dict["value"]

    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

print("*** done recording")
stream.stop_stream()
stream.close()
p.terminate()