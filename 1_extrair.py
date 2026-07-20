import sys
import zipfile
from pathlib import Path

import gdown
import pandas as pd

import banco
from config import (
    ARQUIVOS,
    CSV_ENCODING,
    CSV_SEPARADOR,
    DRIVE_FILE_ID,
    PASTA_DADOS,
    TAMANHO_BLOCO,
)

# -----------------------------------------------------------------------------

COLUNAS_RAW = {
    "viagem": [
        "id_viagem", "num_proposta", "situacao", "viagem_urgente",
        "justificativa_urgencia", "cod_orgao_superior", "nome_orgao_superior",
        "cod_orgao_solicitante", "nome_orgao_solicitante", "cpf_viajante",
        "nome_viajante", "cargo", "funcao", "descricao_funcao",
        "data_inicio", "data_fim", "destinos", "motivo",
        "valor_diarias", "valor_passagens", "valor_devolucao",
        "valor_outros_gastos",
    ],
    "pagamento": [
        "id_viagem", "num_proposta", "cod_orgao_superior", "nome_orgao_superior",
        "cod_orgao_pagador", "nome_orgao_pagador", "cod_ug_pagadora",
        "nome_ug_pagadora", "tipo_pagamento", "valor",
    ],
    "passagem": [
        "id_viagem", "num_proposta", "meio_transporte",
        "pais_origem_ida", "uf_origem_ida", "cidade_origem_ida",
        "pais_destino_ida", "uf_destino_ida", "cidade_destino_ida",
        "pais_origem_volta", "uf_origem_volta", "cidade_origem_volta",
        "pais_destino_volta", "uf_destino_volta", "cidade_destino_volta",
        "valor_passagem", "taxa_servico", "data_emissao", "hora_emissao",
    ],
    "trecho": [
        "id_viagem", "num_proposta", "sequencia_trecho", "origem_data",
        "origem_pais", "origem_uf", "origem_cidade", "destino_data",
        "destino_pais", "destino_uf", "destino_cidade",
        "meio_transporte", "numero_diarias", "missao",
    ],
}

CAMINHO_ZIP = PASTA_DADOS / "transparencia.zip"

# -----------------------------------------------------------------------------

def baixar_zip():
    """Baixa o .zip do Google Drive para data/transparencia.zip (se ainda nao existir)."""
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    if CAMINHO_ZIP.exists():
        print(f"[1/3] Zip ja existe em {CAMINHO_ZIP}, pulando download.")
        return
    try:
        print("[1/3] Baixando .zip do Google Drive...")
        url = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}"
        gdown.download(url, str(CAMINHO_ZIP), quiet=False)
    except Exception as erro:
        raise RuntimeError(
            f"Falha ao baixar o arquivo do Google Drive (ID={DRIVE_FILE_ID}). "
            f"Verifique sua conexao e se o arquivo esta compartilhado como "
            f"'Qualquer pessoa com o link'. Detalhe: {erro}"
        )

# -----------------------------------------------------------------------------

def extrair_zip():
    """Extrai todos os CSVs do .zip para a pasta data/."""
    try:
        print("[2/3] Extraindo CSVs do zip...")
        with zipfile.ZipFile(CAMINHO_ZIP, "r") as z:
            z.extractall(PASTA_DADOS)
    except Exception as erro:
        raise RuntimeError(f"Falha ao extrair o zip {CAMINHO_ZIP}. Detalhe: {erro}")

# -----------------------------------------------------------------------------

def carregar_csv_na_raw(conexao, chave):
    
    info = ARQUIVOS[chave]
    caminho_csv = PASTA_DADOS / info["csv"]
    tabela = info["tabela_raw"]
    colunas = COLUNAS_RAW[chave]

    if not caminho_csv.exists():
        raise RuntimeError(f"Arquivo {caminho_csv} nao encontrado apos extracao.")

    
    banco.executar(conexao, f"TRUNCATE TABLE {tabela};")

    marcadores = ", ".join(["%s"] * len(colunas))
    sql_insert = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({marcadores})"

    total_linhas = 0
    try:
        leitor = pd.read_csv(
            caminho_csv,
            sep=CSV_SEPARADOR,
            encoding=CSV_ENCODING,
            header=0,          
            names=colunas,     
            dtype=str,         
            chunksize=TAMANHO_BLOCO,
        )
        for bloco in leitor:
            
            bloco = bloco.astype(object).where(pd.notnull(bloco), None)  
            linhas = list(bloco.itertuples(index=False, name=None))
            banco.inserir_em_lote(conexao, sql_insert, linhas)
            total_linhas += len(linhas)
            print(f"    -> {tabela}: {total_linhas} linhas carregadas...")
    except Exception as erro:
        raise RuntimeError(f"Falha ao carregar {caminho_csv} em {tabela}. Detalhe: {erro}")

    print(f"[OK] {tabela}: {total_linhas} linhas carregadas no total.")

# -----------------------------------------------------------------------------

def main():
    print("=== FASE 1: Extracao e carga da camada RAW ===")
    try:
        baixar_zip()
        extrair_zip()
    except RuntimeError as erro:
        print(f"ERRO: {erro}")
        sys.exit(1)

    try:
        conexao = banco.conectar()
    except RuntimeError as erro:
        print(f"ERRO: {erro}")
        sys.exit(1)

    try:
        print("[3/3] Carregando CSVs nas tabelas RAW...")
        for chave in ARQUIVOS:
            carregar_csv_na_raw(conexao, chave)
        print("=== FASE 1 concluida com sucesso. ===")
    except RuntimeError as erro:
        print(f"ERRO: {erro}")
        sys.exit(1)
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
