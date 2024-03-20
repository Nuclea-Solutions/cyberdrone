import openai
from openai import OpenAI
import re
import argparse
import os
import json
import time
import cv2
import airsim
import base64
import requests
from airsim_wrapper import *


# Inicialización de la API de OpenAI
client = OpenAI(api_key='API_KEY')

# Análisis de los argumentos de línea de comandos
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="prompts/airsim_basic.txt")
parser.add_argument("--sysprompt", type=str, default="system_prompts/airsim_basic.txt")
args = parser.parse_args()

with open("config.json", "r") as f:
    config = json.load(f)

print("Initializing ChatGPT...")
openai.api_key = config["OPENAI_API_KEY"]

with open(args.sysprompt, "r") as f:
    sysprompt = f.read()




# Establecimiento de la clave de la API de OpenAI
OpenAI.api_key = config["OPENAI_API_KEY"]

client = airsim.MultirotorClient()

png_image = client.simGetImages([airsim.ImageRequest(0, airsim.ImageType.Scene, False, False)])



def analyze_image_with_openai(image, client, custom_prompt):
    base64_image = png_image

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", 
                     "text": "What’s in this image?" #custom_prompt
                     },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "low"
                        }
                    }
                ]
            }
        ],
        max_tokens=300,
        model="gpt-4-vision-preview"
    )
    print(response.choices[0])



# Lectura del prompt de sistema desde un archivo de texto
with open(args.sysprompt, "r") as f:
    sysprompt = f.read()

# Historial del chat para mantener el seguimiento de la conversación
chat_history = [
    {
        "role": "system",
        "content": sysprompt
    },
    {
        "role": "user",
        "content": "move 10 units up"
    },
    {
        "role": "assistant",
        "content": """```python
aw.fly_to([aw.get_drone_position()[0], aw.get_drone_position()[1], aw.get_drone_position()[2]+10])
```"""
    }
]

# Función para enviar una solicitud al chatbot y recibir una respuesta

def ask(prompt):
    chat_history.append(
        {
            "role": "user",
            "content": prompt,
        }
    )
    completion = openai.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=chat_history,
        temperature=0
    )
    chat_history.append(
        {
            "role": "assistant",
            "content": completion.choices[0].message.content,
        }
    )
    return chat_history[-1]["content"]


print(f"Done.")

code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)

# Función para extraer código Python de un mensaje de respuesta del chatbot
def extract_python_code(content):
    code_blocks = re.findall(r"```(.*?)```", content, re.DOTALL)
    if code_blocks:
        full_code = "\n".join(code_blocks)

        if full_code.startswith("python"):
            full_code = full_code[7:]

        return full_code
    else:
        return None

# Inicialización del chatbot de AirSim
print("Initializing AirSim...")
aw = AirSimWrapper()  # Inicializar la instancia de AirSimWrapper
print(f"Done.")

# Lectura del prompt inicial para el chatbot desde un archivo de texto
with open(args.prompt, "r") as f:
    prompt = f.read()

# Inicio de la conversación con el chatbot
ask(prompt)
print("Welcome to the AirSim chatbot! I am ready to help you with your AirSim questions and commands.")

# Bucle principal para interactuar con el chatbot
while True:
    question = input("AirSim> ")

    if question == "!quit" or question == "!exit":
        break

    if question == "!clear":
        os.system("cls")
        continue

    # Envío de la pregunta al chatbot y recepción de la respuesta
    response = ask(question)

    print(f"\n{response}\n")

    # Extracción y ejecución de código Python de la respuesta del chatbot
    code = extract_python_code(response)
    if code is not None:
        print("Please wait while I run the code in AirSim...")
        exec(extract_python_code(response))
        print("Done!\n")

        # Realización de detección de objetos en AirSim utilizando la cámara del dron
        print("Realizando detección de objetos...")
        try:
            aw.perform_object_detection()  # Método para realizar detección de objetos en AirSim
        except Exception as e:
            print(f"Error: {e}")

