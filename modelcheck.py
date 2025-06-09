import google.generativeai as genai

genai.configure(api_key="AIzaSyDkUr7S1ApXITaO8kaW_aqzmdicxfDKKcU")

models = genai.list_models()
for model in models:
    print(model.name)
