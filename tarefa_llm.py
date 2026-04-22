import requests
import json
from openai import OpenAI

API_KEY = "sk-7AJ6A_-aTikSDnMD9UyIxA"

client = OpenAI(
    api_key=API_KEY,
    base_url="http://litellm.datalawyer.local",
    timeout=120
)

url = "http://elastic.datalawyer.local:9200/processo_documentos_trt/_search"

query = {
    "size": 5,
    "query": {
        "bool": {
            "filter": [
                {"term": {"TipoDocumento.raw": "Petição Inicial"}},
                {"term": {"ClasseJudicialCnj1G": "Ação Trabalhista - Rito Ordinário"}}
            ]
        }
    }
}

print("Buscando petições...")

response = requests.get(url, json=query, timeout=60)
data = response.json()

dataset = []

for i, doc in enumerate(data["hits"]["hits"]):

    texto = doc["_source"].get("Texto", "")

    prompt = f" O resumo deve incluir, quando estiverem disponíveis no texto Nome ou identificação do reclamante, Nome ou identificação da reclamada,Tipo de ação trabalhista,Principais fatos narrados, Principais pedidos da ação, Não invente informações que não estejam no texto.:\n\n{texto}"

    print(f"Processando petição {i+1}/5...")

    try:
        gemini = client.chat.completions.create(
            model="vertex_ai/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}]
        )

        resumo_gemini = gemini.choices[0].message.content

    except Exception as e:
        print("Erro no Gemini:", e)
        resumo_gemini = "Erro ao gerar resumo"

    try:
        gpt = client.chat.completions.create(
            model="openai/gpt-5-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        resumo_gpt = gpt.choices[0].message.content

    except Exception as e:
        print("Erro no GPT:", e)
        resumo_gpt = "Erro ao gerar resumo"

    dataset.append({
        "data": {
            "peticao": texto,
            "modelo_a": resumo_gemini,
            "modelo_b": resumo_gpt
        }
    })

with open("dataset_labelstudio.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print("Dataset criado com sucesso!")