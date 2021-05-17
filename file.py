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


def convert_to_hex(value):
    array = value.split(",")
    # new_array = []
    # for i in array:
    #     converted = hex(int(i)).split("x")[-1]
    #     # print(converted)
    #     new_array.append(converted)
    return f"#{int(array[0]):02x}{int(array[1]):02x}{int(array[2]):02x}"


# Set up MQTT client
client = mqtt.Client()
client.connect("192.168.100.250", 1883)

colour = None


devices = [
    # {"name": "tvlamp2", "topic": "cmnd/tasmota_713AB3/Backlog", "type": "tasmota"},
    # {"name": "tvlamp1", "topic": "cmnd/tasmota_713A6F/Backlog", "type": "tasmota"},
    {"name": "office_lamp", "topic": "cmnd/tasmota_713A9E/Backlog", "type": "tasmota"},
    {
        "name": "office_led_strip",
        "topic": "zigbee2mqtt/LED Strip/set",
        "type": "zigbee",
    },
    # {
    #     "name": "kitchen_led_strip",
    #     "topic": "zigbee2mqtt/Kitchen LED Strip/set",
    #     "type": "zigbee",
    # },
    # {"name": "wled", "topic": "wled/5m/col", "colour": convert_to_hex(colour)},
]


def get_device_config(type, colour):
    if type == "tasmota":
        return (
            f"NoDelay;Fade 0;NoDelay;Speed 0;NoDelay;Dimmer 100;NoDelay;Color2 {colour}"
        )
    if type == "zigbee":
        return json.dumps(
            {
                "state": "ON",
                "brightness": 255,
                "transition": 0.001,
                "color": {"rgb": colour},
            }
        )


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


# Set constants for audio input
BUFFER_SIZE = 1024
CHANNELS = 1
FORMAT = pyaudio.paFloat32
METHOD = "default"
SAMPLE_RATE = 44100
HOP_SIZE = BUFFER_SIZE // 2
PERIOD_SIZE_IN_FRAME = HOP_SIZE

# Initialise pyAudio
p = pyaudio.PyAudio()


mic_input = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=PERIOD_SIZE_IN_FRAME,
)

tempo_detect = aubio.tempo(METHOD, BUFFER_SIZE, HOP_SIZE, SAMPLE_RATE)

pitch_detect = aubio.pitch(METHOD, BUFFER_SIZE, HOP_SIZE, SAMPLE_RATE)
pitch_detect.set_unit("Hz")
pitch_detect.set_silence(-40)

print("Listening to mic...")

# Set variable for last colour used
last_colour = ""

# Set Tasmota settings
# client.publish("cmnd/officelamp/Fade", "0")
# client.publish("cmnd/officelamp/Speed", "0")

while True:
    try:
        audio_buffer = mic_input.read(PERIOD_SIZE_IN_FRAME)
        samples = np.frombuffer(audio_buffer, dtype=aubio.float_type)

        # Detect a beat
        is_beat = tempo_detect(samples)

        # Get the pitch
        pitch = pitch_detect(samples)[0]

        # Get the volume
        volume = np.sum(samples ** 2) / len(samples)

        if is_beat[0]:
            print(pitch, volume)
            colour_dict = change_colour(pitch)
            while colour_dict["value"] == last_colour:
                colour_dict = change_colour(pitch)
            colour = colour_dict["value"]
            # if pitch < 100:
            #     colour = "255,0,0"
            print(f"Setting colour to {colour}")
            for device in devices:
                client.publish(
                    device["topic"], get_device_config(device["type"], colour)
                )
            # client.publish(
            #     "zigbee2mqtt/Kitchen LED Strip/set",
            #     json.dumps(
            #         {
            #             "state": "ON",
            #             "brightness": 255,
            #             "transition": 0.001,
            #             "color": {"rgb": colour},
            #         }
            #     ),
            # )
            # client.publish("cmnd/tvlamp/Color2", colour)
            # client.publish("cmnd/tvlamp2/Color2", colour)
            # print(convert_to_hex(colour))
            # client.publish("wled/5m/col", convert_to_hex(colour))
            # client.publish(topic2, colour)
            # client.publish("cmnd/tvlamp/Color2", colour_dict["value"])
            # client.publish("cmnd/tvlamp2/Color2", colour_dict["value"])
            last_colour = colour

    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

print("*** done recording")
mic_input.stop_mic_input()
mic_input.close()
p.terminate()