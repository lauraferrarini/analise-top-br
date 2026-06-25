import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import traceback
import sys

URL = "https://www.letras.mus.br/mais-acessadas/"
PASTA_DADOS = "historico_dados"
PASTA_RELATORIOS = "historico_relatorios"
RELATORIO_RAIZ = "relatorio_diario.md"
MARGEM_OSCILACAO = 2 

os.makedirs(PASTA_DADOS, exist_ok=True)
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

def extrair_musicas():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status() # Força erro se o site bloquear o robô (ex: erro 403 ou 503)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    musicas_atuais = {}
    lista_top = soup.find('ol', class_='top-list_mus')
    
    if not lista_top:
        print("⚠️ Alerta: A estrutura HTML do Letras mudou ou fomos bloqueados por um captcha.")
        return musicas_atuais
        
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
    data_hoje_iso = datetime.now().strftime("%Y-%m-%d")
    
    if os.path.exists(PASTA_DADOS):
        arquivos = sorted([
            f for f in os.listdir(PASTA_DADOS) 
            if f.endswith('.json') and f != f"dados_{data_hoje_iso}.json"
        ])
        if arquivos:
            ultimo_arquivo = os.path.join(PASTA_DADOS, arquivos[-1])
            with open(ultimo_arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
            
    if os.path.exists("dados_anteriores.json"):
        with open("dados_anteriores.json", 'r', encoding='utf-8') as f:
            return json.load(f)
            
    return {}

def gerar_relatorio():
    atuais = extrair_musicas()
    
    if not atuais:
        print("❌ Erro: Nenhuma música pôde ser extraída do site. Abortando.")
        sys.exit(1)
        
    anteriores = buscar_dados_anteriores()
    
    data_hoje_iso = datetime.now().strftime("%Y-%m-%d")
    data_hoje_br = datetime.now().strftime("%d/%m/%Y")

    novas_entradas = []
    subidas_absurdas = []   
    grandes_saltos = []     
    subidas_moderadas = []  
    pequenas_subidas = []   

    if not anteriores:
        conteudo_md = f"# 📊 Relatório Letras.mus.br - {data_hoje_br}\n\n"
        conteudo_md += "ℹ️ **Primeira execução detectada com sucesso!**\n"
        conteudo_md += "O sistema estruturou a base de dados inicial hoje. A partir de amanhã, todas as movimentações aparecerão aqui automaticamente.\n\n"
        conteudo_md += "### 📋 Prévia do Top 10 Atual:\n"
        for i, (chave, m) in enumerate(atuais.items(), start=1):
            if i > 10: break
            conteudo_md += f"{i}º. **{m['nome']}** — *{m['artista']}*\n"
    else:
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

        subidas_absurdas.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)
        grandes_saltos.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)
        subidas_moderadas.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)
        pequenas_subidas.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)

        conteudo_md = f"# 📊 Relatório Letras.mus.br - {data_hoje_br}\n\n"
        
        if subidas_absurdas:
            conteudo_md += "## 🚨 🚨 EXPLOSÃO NO TOP: SUBIDAS ABSURDAS (+400 posições) 🚨 🚨\n"
            for m in subidas_absurdas:
                conteudo_md += f"> ### 💥 **{m['dados']['nome']}** — *{m['dados']['artista']}*\n"
                conteudo_md += f"> 🛑 **Subida histórica!** Saltou de {m['pos_anterior']}º direto para **{m['pos_atual']}º** (🔼 **+{m['posicoes_ganhas']}** posições de ontem para hoje!)\n\n"
        
        conteudo_md += "## 🔥 Grandes Saltos (+200 a 400 posições)\n"
        if grandes_saltos:
            for m in grandes_saltos:
                conteudo_md += f"- **{m['dados']['nome']}** ({m['dados']['artista']}): Subiu de {m['pos_anterior']}º para **{m['pos_atual']}º** (🔥 +{m['posicoes_ganhas']} posições)\n"
        else:
            conteudo_md += "- Nenhuma música com grande salto nesta faixa hoje.\n"

        conteudo_md += "\n## 📈 Subidas Significativas (100 a 200 posições)\n"
        if subidas_moderadas:
            for m in subidas_moderadas:
                conteudo_md += f"- **{m['dados']['nome']}** ({m['dados']['artista']}): Subiu de {m['pos_anterior']}º para **{m['pos_atual']}º** (📈 +{m['posicoes_ganhas']} posições)\n"
        else:
            conteudo_md += "- Nenhuma subida nesta faixa hoje.\n"

        conteudo_md += f"\n## 🌱 Pequenas Subidas (Abaixo de 100 posições)\n"
        conteudo_md += f"> Omitindo oscilações menores ou iguais a {MARGEM_OSCILACAO} posições.\n\n"
        if pequenas_subidas:
            for m in pequenas_subidas:
                conteudo_md += f"- **{m['dados']['nome']}** ({m['dados']['artista']}): {m['pos_anterior']}º → **{m['pos_atual']}º** (+{m['posicoes_ganhas']})\n"
        else:
            conteudo_md += "- Sem oscilações relevantes para cima hoje.\n"

        conteudo_md += "\n## 🚀 Novas Entradas no Top\n"
        if novas_entradas:
            for m in novas_entradas:
                conteudo_md += f"- **{m['nome']}** ({m['artista']}) - Apareceu direto na posição **{m['posicao']}º**\n"
        else:
            conteudo_md += "- Nenhuma música inédita detectada hoje.\n"

    caminho_relatorio_historico = os.path.join(PASTA_RELATORIOS, f"relatorio_{data_hoje_iso}.md")
    with open(caminho_relatorio_historico, 'w', encoding='utf-8') as f:
        f.write(conteudo_md)

    with open(RELATORIO_RAIZ, 'w', encoding='utf-8') as f:
        f.write(conteudo_md)

    caminho_dados_historico = os.path.join(PASTA_DADOS, f"dados_{data_hoje_iso}.json")
    with open(caminho_dados_historico, 'w', encoding='utf-8') as f:
        json.dump(atuais, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    try:
        gerar_relatorio()
        print("Análise inteligente concluída com sucesso!")
    except Exception as e:
        print("\n💥 --- ERRO CRÍTICO DETECTADO NO SCRIPT --- 💥")
        traceback.print_exc() # Imprime o erro detalhado no log do GitHub
        sys.exit(1)
