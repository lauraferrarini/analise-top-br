import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

URL = "https://www.letras.mus.br/mais-acessadas/"
ARQUIVO_DADOS = "dados_anteriores.json"
ARQUIVO_RELATORIO = "relatorio_diario.md"
MARGEM_OSCILACAO = 2 # Ignora subidas menores ou iguais a 2 posições

def extrair_musicas():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    musicas_atuais = {}
    
    # O Letras utiliza <ol class="top-list_mus"> para a lista de músicas
    lista_top = soup.find('ol', class_='top-list_mus')
    
    if lista_top:
        itens = lista_top.find_all('li')
        for rank, item in enumerate(itens, start=1):
            # Extrai o nome da música e do artista
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

def gerar_relatorio():
    atuais = extrair_musicas()
    anteriores = {}
    
    # Carrega dados do dia anterior
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
            anteriores = json.load(f)

    novas_entradas = []
    subiram = []

    # Compara os dados
    for chave, dados_atuais in atuais.items():
        pos_atual = dados_atuais['posicao']
        
        if chave not in anteriores:
            novas_entradas.append(dados_atuais)
        else:
            pos_anterior = anteriores[chave]['posicao']
            diferenca = pos_anterior - pos_atual # Se for positivo, a música subiu
            
            if diferenca > MARGEM_OSCILACAO:
                subiram.append({
                    "dados": dados_atuais,
                    "pos_anterior": pos_anterior,
                    "pos_atual": pos_atual,
                    "posicoes_ganhas": diferenca
                })

    # Cria o relatório em Markdown
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    with open(ARQUIVO_RELATORIO, 'w', encoding='utf-8') as f:
        f.write(f"# 📊 Relatório Letras.mus.br - {data_hoje}\n\n")
        
        f.write("## 🚀 Novas Entradas no Top\n")
        if novas_entradas:
            for m in novas_entradas:
                f.write(f"- **{m['nome']}** ({m['artista']}) - Entrou na posição **{m['posicao']}º**\n")
        else:
            f.write("- Nenhuma nova entrada expressiva hoje.\n")
            
        f.write("\n## 📈 Subidas Significativas\n")
        f.write(f"> Ignorando oscilações de até {MARGEM_OSCILACAO} posições.\n\n")
        if subiram:
            # Ordena por quem ganhou mais posições
            subiram.sort(key=lambda x: x['posicoes_ganhas'], reverse=True)
            for m in subiram:
                nome = m['dados']['nome']
                artista = m['dados']['artista']
                f.write(f"- **{nome}** ({artista}): Subiu de {m['pos_anterior']}º para **{m['pos_atual']}º** (🔼 +{m['posicoes_ganhas']} posições)\n")
        else:
            f.write("- Nenhuma subida expressiva hoje.\n")

    # Salva os dados de hoje para o dia seguinte
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(atuais, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    gerar_relatorio()
    print("Análise concluída e relatório gerado!")
