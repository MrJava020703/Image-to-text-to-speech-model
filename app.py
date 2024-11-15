import os
import time
from typing import Any

import requests
import streamlit as st
from dotenv import find_dotenv, load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from transformers import pipeline

from utils.custom import css_code

load_dotenv(find_dotenv())
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def progress_bar(amount_of_time: int) -> Any:
    """
    A very simple progress bar the increases over time,
    then disappears when it reached completion
    :param amount_of_time: time taken
    :return: None
    """
    progress_text = "Please wait, Generative models hard at work"
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(amount_of_time):
        time.sleep(0.04)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()


def generate_text_from_image(url: str) -> str:
    """
    A function that uses the blip model to generate text from an image.
    :param url: image location
    :return: text: generated text from the image
    """
    image_to_text: Any = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")

    generated_text: str = image_to_text(url)[0]["generated_text"]

    print(f"IMAGE INPUT: {url}")
    print(f"GENERATED TEXT OUTPUT: {generated_text}")
    return generated_text


def generate_story_from_text(scenario: str) -> str:
    """
    A function using a prompt template and GPT to generate a short story. LangChain is also
    used for chaining purposes
    :param scenario: generated text from the image
    :return: generated story from the text
    """
    prompt_template: str = f"""
    You are a story teller;
    You can generate a short story based on a simple narrative, the story should be no more than 20 words;
    
    CONTEXT: {scenario}
    STORY:
    """

    prompt: PromptTemplate = PromptTemplate(template=prompt_template, input_variables=["scenario"])

    llm: Any = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=1)

    story_llm: Any = LLMChain(llm=llm, prompt=prompt, verbose=True)

    generated_story: str = story_llm.predict(scenario=scenario)

    print(f"TEXT INPUT: {scenario}")
    print(f"GENERATED STORY OUTPUT: {generated_story}")
    return generated_story


def generate_speech_from_text(message: str) -> Any:
    """
    A function using the ESPnet text to speech model from HuggingFace
    :param message: short story generated by the GPT model
    :return: generated audio from the short story
    """
    API_URL: str = "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits"
    headers: dict[str, str] = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    payloads: dict[str, str] = {
        "inputs": message
    }

    response: Any = requests.post(API_URL, headers=headers, json=payloads)
    with open("generated_audio.flac", "wb") as file:
        file.write(response.content)


def main() -> None:
    """
    Main function
    :return: None
    """
    st.set_page_config(page_title="Image to audio story", page_icon="img/webworks87-favicon-light.png", layout="wide")

    st.markdown(css_code, unsafe_allow_html=True)

    with st.sidebar:
        st.image("img/logo.jpg")
        st.write("---")
        st.write("App created by Tech DareDevils")

    st.header("Generate an audio story from an image")
    uploaded_file: Any = st.file_uploader("Please choose a file to upload", type="jpg")

    if uploaded_file is not None:
        print(uploaded_file)
        bytes_data: Any = uploaded_file.getvalue()
        with open(uploaded_file.name, "wb") as file:
            file.write(bytes_data)
        st.image(uploaded_file, caption="Uploaded Image",
                 use_column_width=True)
        progress_bar(100)
        scenario: str = generate_text_from_image(uploaded_file.name)
        story: str = generate_story_from_text(scenario)
        generate_speech_from_text(story)

        with st.expander("Generated scenario"):
            st.write(scenario)
        with st.expander("Generated story"):
            st.write(story)

        st.audio("generated_audio.flac")


if __name__ == "__main__":
    main()
