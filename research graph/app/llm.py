import json
import os
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import find_file, get_secret

BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = os.environ.get("PREP_MODEL", "nvidia/nemotron-3-super-120b-a12b")

EXTRA_BODY = {"chat_template_kwargs": {"enable_thinking": True}}

JSON_MAX_TOKENS = 5000
TEXT_MAX_TOKENS = 8000
TOOLS_MAX_TOKENS = 4000

TEXT_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 2

JSON_SYSTEM_PROMPT = (
    "You are a precise data extraction engine.\n"
    "Reply with a single valid JSON object and nothing else.\n"
    "No markdown code fences, no commentary, no explanation before or after.\n"
    "Use exactly the key names the user specifies.\n"
    "Always write in English."
)

TEXT_SYSTEM_PROMPT = (
    "You are an interview preparation writer for software engineers.\n"
    "Always write in clear, professional English. Never use Hindi, Urdu or "
    "Hinglish, even if the instructions you receive contain them.\n"
    "Use only the material you are given. Never invent facts, links or "
    "statistics. If something is not covered by the material, say so plainly.\n"
    "Be concise and practical."
)


def load_api_key():
    key = get_secret("NVIDIA_API_KEY")
    if key:
        return key

    keyfile = find_file("apikey.md")
    if keyfile is not None:
        found = re.search(r"nvapi-[A-Za-z0-9_\-]+", keyfile.read_text())
        if found:
            return found.group(0)

    raise RuntimeError("NVIDIA_API_KEY nahi mila. .env mein daalo.")


llm = ChatOpenAI(
    model=MODEL,
    base_url=BASE_URL,
    api_key=load_api_key(),
    extra_body=EXTRA_BODY,
    timeout=180.0,
    max_retries=1,
)


def strip_code_fence(text):

    if text is None:
        text = ""

    text = str(text).strip()

    if text.startswith("```"):
        lines = text.split("\n")[1:]

        if len(lines) > 0 and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines)

    return text.strip()


def read_answer(message):

    text = strip_code_fence(message.content)
    if text != "":
        return text

    for holder in ["additional_kwargs", "response_metadata"]:
        box = getattr(message, holder, None) or {}
        thinking = box.get("reasoning_content")
        if thinking:
            return strip_code_fence(thinking)

    return ""


def finish_reason_of(message):
    meta = getattr(message, "response_metadata", None) or {}
    return meta.get("finish_reason")


def ask_with_tools(system_prompt, user_prompt, tools):

    model_with_tools = llm.bind_tools(
        tools,
        tool_choice="auto",
        max_tokens=TOOLS_MAX_TOKENS,
        temperature=0.2,
    )

    answer = model_with_tools.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])


    return answer.tool_calls or []


def ask_json(prompt, required_keys):

    model = llm.bind(temperature=0.2, max_tokens=JSON_MAX_TOKENS)
    message = prompt

    for attempt in [1, 2]:
        answer = model.invoke([
            SystemMessage(content=JSON_SYSTEM_PROMPT),
            HumanMessage(content=message),
        ])
        text = read_answer(answer)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print("   [llm] JSON nahi aaya, dobara poochte hain (" + str(attempt) + "/2)")
            message = prompt + "\n\nYour previous reply was not valid JSON. Return only JSON."
            continue

        missing = []
        for key in required_keys:
            if key not in data:
                missing.append(key)

        if len(missing) == 0:
            return data

        print("   [llm] ye keys missing thi: " + str(missing) + ", dobara poochte hain")
        message = (prompt + "\n\nYour previous reply was missing these keys: "
                   + str(missing) + ". Use exactly these key names.")

    raise RuntimeError("LLM ne do baar galat JSON diya")


def ask_text(prompt):

    model = llm.bind(temperature=0.4, max_tokens=TEXT_MAX_TOKENS)
    finish_reason = None

    for attempt in range(1, TEXT_ATTEMPTS + 1):
        answer = model.invoke([
            SystemMessage(content=TEXT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        text = read_answer(answer)
        finish_reason = finish_reason_of(answer)

        if text != "":
            print("   [llm] jawab mila: " + str(len(text)) + " characters | finish="
                  + str(finish_reason))
            return text

        print("   [llm] khaali jawab aaya (finish=" + str(finish_reason)
              + "), dobara poochte hain (" + str(attempt) + "/"
              + str(TEXT_ATTEMPTS) + ")")

        if attempt < TEXT_ATTEMPTS:
            time.sleep(RETRY_WAIT_SECONDS)

    raise RuntimeError(
        "LLM ne " + str(TEXT_ATTEMPTS) + " baar khaali jawab diya "
        "(finish_reason=" + str(finish_reason) + "). Ye model ki apni "
        "dikkat hai, prompt ki nahi."
    )
