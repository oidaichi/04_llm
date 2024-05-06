# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 12:45:57 2024

@author: user
"""

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

# LangChainのCallbacksを使うことで、標準出力をストリーミングにすることができる。
chat = ChatOpenAI(model="gpt-3.5-turbo",
                  temperature=0.0,
                  streaming=True,
                  callbacks=[StreamingStdOutCallbackHandler()] # ここが重要
                  )

messages = [HumanMessage(content="自己紹介してください。")]
result = chat(messages)


# ChatPromptTemplate。これでFew-Shot-Learningを実現するプロンプトを与えることができる。
from langchain.prompts import ChatPromptTemplate, PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage

system_template = """
あなたはプロのシステムエンジニア兼証券アナリストになってください。
"""

human_template = """
日本の株式市場に上場している会社名を入力したら、その会社のホームページを検索し、さらにそのホームページの中からIR資料を見つけて来てください。
そのIR資料から直近の業績を調べ、要約してください。
会社名：{company_name}
"""

chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template(human_template)])

messages = chat_prompt.format_prompt(company_name="やまみ").to_messages()
result2 = chat(messages)