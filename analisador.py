import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

URL = "https://www.letras.mus.br/mais-acessadas/"
PASTA_DADOS = "historico_dados"
PASTA_RELATORIOS = "historico_relatorios"
RELATORIO_RAIZ = "relatorio_diario.md" # Mantém o último relatório na raiz para acesso rápido
MARGEM_OSCILACAO = 2 

# Garante que as pastas de histórico existam
os.makedirs(PASTA_DADOS, exist_ok=True)
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

def extrair_musicas():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    musicas_atuais = {}
    lista_top = soup.find('ol', class_='top-list_mus')
    
    if lista_top:
        itens = lista_top.find_all('li')
        for rank, item in enumerate(itens, start=1):
            tag_nome = item.find('b')
            tag_artista = item.find('span')
            
            nome = tag_nome.text.strip() if tag_nome else "Desconhecido"
            artista = tag_artista.text.strip() if tag_artista else "Desconhecido"
            
            chave = f"{nome} - {artista}"
            musicas_atuais[chave] = {
                "posicao": rank,
                "nome": nome,
                "artista": artista
            }
            
    return musicas_atuais

def buscar_dados_anteriores():
    # Procura o arquivo JSON mais recente na pasta de histórico
    arquivos = sorted([f for f in os.listdir(PASTA_DADOS) if f.endswith('.json')])
    if arquivos:
        ultimo_arquivo = os.path.join(PASTA_DADOS, arquivos[-1])
        with open(ultimo_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def gerar_relatorio():
    atuais = extrair_musicas()
    anteriores = buscar_dados_anteriores()
    
    data_hoje_iso = datetime.now().strftime("%Y-%m-%d")
    data_hoje_br = datetime.now().strftime("%d/%m/%Y")

    novas_entradas = []
    
    # Categorias de subidas
    subidas_absurdas = []   # > 400 posições
    grandes_saltos = []     # > 200 e <= 400 posições
    subidas_moderadas = []  # >= 100 e <= 200 posições
    pequenas_subidas = []   # > MARGEM_OSCILACAO e < 100 posições

    # Compara os dados
    for chave, dados_atuais in atuais.items():
        pos_atual = dados_atuais['posicao']
        
        if chave not in anteriores:
            novas_entradas.append(dados_atuais)
        else:
            pos_anterior = anteriores[chave]['posicao']
            diferenca = pos_anterior - pos_atual 
            
            dados_item = {
                "dados": dados_atuais,
                "pos_anterior": pos_anterior,
                "pos_atual": pos_atual,
                "posicoes_ganhas": diferenca
            }

            if diferenca > 400:
                subidas_absurdas.append(dados_item)
            elif diferenca > 200:
                grandes_saltos.append(dados_item)
            elif diferenca >= 100:
                subidas_moderadas.append(dados_item)
            elif diferenca > MARGEM_OSCILACAO:
                pequenas_subidas.append(dados_item)

    # Ordena as listas por quem subiu mais
    subidas_absurdas.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)
    grandes_saltos.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)
    subidas_moderadas.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)
    pequenas_subidas.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)

    # Monta o corpo do relatório em Markdown
    conteudo_md = f"# 📊 Relatório Letras.mus.br - {data_hoje_br}\n\n"
    
    # 1. Seção de Subidas Absurdas
    if subidas_absurdas:
        conteudo_md += "## 🚨 🚨 EXPLOSÃO NO TOP: SUBIDAS ABSURDAS (+400 posições) 🚨 🚨\n"
        for m in subidas_absurdas:
            conteudo_md += f"> ### 💥 **{m['dados']['nome']}** — *{m['dados']['artista']}*\n"
            conteudo_md += f"> 🛑 **Subida histórica!** Saltou de {m['pos_anterior']}º direto para **{m['pos_atual']}º** (🔼 **+{m['posicoes_ganhas']}** posições de ontem para hoje!)\n\n"
    
    # 2. Seção de Grandes Saltos
    conteudo_md += "## 🔥 Grandes Saltos (+200 a 400 posições)\n"
    if grandes_saltos:
        for m in grandes_saltos:
            conteudo_md += f"- **{m['dados']['nome']}** ({m['dados']['artista']}): Subiu de {m['pos_anterior']}º para **{m['pos_atual']}º** (🔥 +{m['posicoes_ganhas']} posições)\n"
    else:
        conteudo_md += "- Nenhuma música com grande salto nesta faixa hoje.\n"

    # 3. Seção de Subidas Moderadas
    conteudo_md += "\n## 📈 Subidas Significativas (100 a 200 posições)\n"
    if subidas_moderadas:
        for m in subidas_moderadas:
            conteudo_md += f"- **{m['dados']['nome']}** ({m['dados']['artista']}): Subiu de {m['pos_anterior']}º para **{m['pos_atual']}º** (📈 +{m['posicoes_ganhas']} posições)\n"
    else:
        conteudo_md += "- Nenhuma subida nesta faixa hoje.\n"

    # 4. Seção de Pequenas Subidas
    conteudo_md += f"\n## 🌱 Pequenas Subidas (Abaixo de 100 posições)\n"
    conteudo_md += f"> Omitindo oscilações menores ou iguais a {MARGEM_OSCILACAO} posições.\n\n"
    if pequenas_subidas:
        for m in pequenas_subidas:
            conteudo_md += f"- **{m['dados']['nome']}** ({m['dados']['artista']}): {m['pos_anterior']}º → **{m['pos_atual']}º** (+{m['posicoes_ganhas']})\n"
    else:
        conteudo_md += "- Sem oscilações relevantes para cima hoje.\n"

    # 5. Seção de Novas Entradas
    conteudo_md += "\n## 🚀 Novas Entradas no Top\n"
    if novas_entradas:
        for m in novas_entradas:
            conteudo_md += f"- **{m['nome']}** ({m['artista']}) - Apareceu direto na posição **{m['posicao']}º**\n"
    else:
        conteudo_md += "- Nenhuma música inédita detectada hoje.\n"

    # Grava o relatório datado no histórico
    caminho_relatorio_historico = os.path.join(PASTA_RELATORIOS, f"relatorio_{data_hoje_iso}.md")
    with open(caminho_relatorio_historico, 'w', encoding='utf-8') as f:
        f.write(conteudo_md)

    # Grava uma cópia na raiz para você ver o último de forma prática
    with open(RELATORIO_RAIZ, 'w', encoding='utf-8') as f:
        f.write(conteudo_md)

    # Salva o JSON datado no histórico para servir de base amanhã
    caminho_dados_historico = os.path.join(PASTA_DADOS, f"dados_{data_hoje_iso}.json")
    with open(caminho_dados_historico, 'w', encoding='utf-8') as f:
        json.dump(atuais, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    gerar_relatorio()
    print("Análise inteligente concluída com histórico atualizado!")
