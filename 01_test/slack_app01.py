import os
import re
import time
from typing import Any
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
from datetime import timedelta
from langchain.memory import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.base import Runnable
from langchain.schema import HumanMessage, LLMResult, SystemMessage, messages_to_dict, messages_from_dict

CHAT_UPDATE_INTERVAL_SEC = 1

load_dotenv()

# ボットトークンとソケットモードハンドラーを使ってアプリを初期化します。
# app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
app = App(
    signing_secret = os.environ["SLACK_SIGNING_SECRET"],
    token = os.environ["SLACK_BOT_TOKEN"],
    process_before_response=True,
    )

class SlackStreamingCallbackHandler(BaseCallbackHandler):
    last_send_time = time.time()
    message = ""
    
    def __init__(self, channel, ts):
        self.channel = channel
        self.ts = ts
    
    def on_llm_new_token(self, token:str, **kwargs) -> None:
        self.message += token
        
        now = time.time()
        if now - self.last_send_time > CHAT_UPDATE_INTERVAL_SEC:
            self.last_send_time = now
            app.client.chat_update(
                channel=self.channel, ts=self.ts, text=f"{self.message}...")
                
    def on_llm_end(self, response:LLMResult, **kwargs: Any) -> Any:
        app.client.chat_update(channel=self.channel, ts=self.ts, text=self.message)




# @app.event("app_mention")
def handle_mention(event, say):
    user = event["user"]
    channel = event["channel"]
    thread_ts = event["ts"]
    id_ts = event["ts"]
    message = re.sub("<@.*>", "", event["text"])

    if "thread_ts" in event:
        id_ts = event["thread_ts"]
    
    result = say("\n\nTyping...", thread_ts=thread_ts)
    ts = result["ts"]

    history = ChatMessageHistory(id_ts=id_ts)

    # clientの履歴を取得して、会話履歴を保存する
    system_message="あなたは最高のアイディアを出すことができるアイディアアシスタントです。"
    # messages = ChatMessageHistory(messages=[SystemMessage(content=system_message)])
    messages = [SystemMessage(content=system_message)]

    messages.extend(history.messages)
    messages.append(HumanMessage(content=message))

    history.add_user_message(message)


    # messages = [SystemMessage(content="You are a helpful assistant.")]
    # messages.extend(history.messages)
    # messages.append(HumanMessage(content=message))

    
    callback = SlackStreamingCallbackHandler(channel=channel, ts=ts)
    
    llm = ChatOpenAI(
        model_name=os.environ["OPENAI_API_MODEL"],
        temperature=os.environ["OPENAI_API_TEMPERATURE"],
        streaming=True,
        callbacks=[callback],
        )
        
    # response = llm.invoke(message)
    # # say(thread_ts=thread_ts, text=f"Hello <@{user}>!")
    # print(response)

    # history.add_ai_message(response.content)

    # message_list = history.messages
    # message_dict = messages_to_dict(message_list)

    # messages_list_dict = messages_from_dict(message_dict)
    # print(messages_list_dict)
    
    # human_message = HumanMessage(content=message)

    # human_message_processor = HumanMessageProcessor(llm)
    # chain = human_message_processor | StrOutputParser()

    # chain = human_message | llm | StrOutputParser()

    ai_message = llm.invoke(messages)
    history.add_message(ai_message)
    
    say(text=ai_message.content, thread_ts=thread_ts)

def just_ack(ack):
    ack()

app.event("app_mention")(ack=just_ack, lazy=[handle_mention])

# ソケットモードハンドラーを使ってアプリを起動します。
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
