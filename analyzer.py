from openai import OpenAI

from prompts import (
    SYSTEM_PROMPT,
    build_analysis_prompt
)


class DocumentAnalyzer:

    def __init__(self, api_key):

        self.client = OpenAI(api_key=api_key)

    def analyze(self, document_text):

        prompt = build_analysis_prompt(document_text)

        response = self.client.chat.completions.create(
            model="gpt-5-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content
