import asyncio
from google import genai
from google.genai import types
from app.config import settings

class Gemini:
    def __init__(self):
        self.client=genai.Client(api_key=settings.gemini_api_key); self.model=settings.gemini_model
    async def text(self,prompt,system,items=None):
        contents=[]
        for x in items or []:
            role='model' if x['role']=='assistant' else 'user'
            contents.append(types.Content(role=role,parts=[types.Part.from_text(text=x['content'])]))
        contents.append(types.Content(role='user',parts=[types.Part.from_text(text=prompt)]))
        r=await asyncio.to_thread(self.client.models.generate_content,model=self.model,contents=contents,config=types.GenerateContentConfig(system_instruction=system,temperature=.4))
        return r.text or 'Нет ответа'
    async def bytes(self,data,mime,prompt):
        r=await asyncio.to_thread(self.client.models.generate_content,model=self.model,contents=[types.Part.from_bytes(data=data,mime_type=mime),prompt])
        return r.text or 'Нет ответа'
    async def search(self,q):
        r=await asyncio.to_thread(self.client.models.generate_content,model=self.model,contents=q,config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())],system_instruction='Отвечай на русском, используй свежие источники и перечисли их в конце.'))
        return r.text or 'Нет ответа'
gemini=Gemini()
