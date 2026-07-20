import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation

import banco
from config import TAMANHO_BLOCO

# -----------------------------------------------------------------------------

def converter_valor(texto):
    
    if texto is None:
        return None
    texto = str(texto).strip()
    if texto == "" or texto.lower() == "nan":
        return None
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(texto).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


# -----------------------------------------------------------------------------

def converter_data(texto):
    
    if texto is None:
        return None
    texto = str(texto).strip()
    if texto == "" or texto.lower() == "nan":
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None

# -----------------------------------------------------------------------------

def texto_ou_none(texto):
    
    if texto is None:
        return None
    texto = str(texto).strip()
    if texto == "" or texto.lower() == "nan":
        return None
    return texto


# -----------------------------------------------------------------------------

def ler_raw_em_blocos(conexao, sql_select):
    cursor = conexao.cursor(dictionary=True, buffered=True)
    cursor.execute(sql_select)
    while True:
        bloco = cursor.fetchmany(TAMANHO_BLOCO)
        if not bloco:
            break
        yield bloco
    cursor.close()


# -----------------------------------------------------------------------------

def transformar_viagem(conexao):
    sql_insert = """
        INSERT INTO silver_viagem (
            id_viagem, num_proposta, situacao, viagem_urgente,
            cod_orgao_superior, nome_orgao_superior, nome_viajante, cargo,
            data_inicio, data_fim, destinos, motivo,
            valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos,
            valor_total, duracao_dias
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    ids_vistos = set()
    ids_validos = set()
    total_inseridas, total_descartadas = 0, 0

    for bloco in ler_raw_em_blocos(conexao, "SELECT * FROM raw_viagem"):
        linhas = []
        for linha in bloco:
            id_viagem = texto_ou_none(linha["id_viagem"])
            nome_orgao_superior = texto_ou_none(linha["nome_orgao_superior"])

            
            if id_viagem is None or nome_orgao_superior is None:
                total_descartadas += 1
                continue
            
            if id_viagem in ids_vistos:
                total_descartadas += 1
                continue
            ids_vistos.add(id_viagem)
            ids_validos.add(id_viagem)

            data_inicio = converter_data(linha["data_inicio"])
            data_fim = converter_data(linha["data_fim"])

            valor_diarias = converter_valor(linha["valor_diarias"]) or Decimal("0.00")
            valor_passagens = converter_valor(linha["valor_passagens"]) or Decimal("0.00")
            valor_devolucao = converter_valor(linha["valor_devolucao"]) or Decimal("0.00")
            valor_outros_gastos = converter_valor(linha["valor_outros_gastos"]) or Decimal("0.00")

            valor_total = valor_diarias + valor_passagens + valor_devolucao + valor_outros_gastos

            duracao_dias = None
            if data_inicio and data_fim and data_fim >= data_inicio:
                duracao_dias = (data_fim - data_inicio).days + 1

            linhas.append((
                id_viagem,
                texto_ou_none(linha["num_proposta"]),
                texto_ou_none(linha["situacao"]),
                texto_ou_none(linha["viagem_urgente"]),
                texto_ou_none(linha["cod_orgao_superior"]),
                nome_orgao_superior,
                texto_ou_none(linha["nome_viajante"]),
                texto_ou_none(linha["cargo"]),
                data_inicio,
                data_fim,
                texto_ou_none(linha["destinos"]),
                texto_ou_none(linha["motivo"]),
                valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos,
                valor_total, duracao_dias,
            ))

        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total_inseridas += len(linhas)

    print(f"[OK] silver_viagem: {total_inseridas} inseridas, {total_descartadas} descartadas.")
    return ids_validos

# -----------------------------------------------------------------------------

def transformar_pagamento(conexao, ids_validos):
    sql_insert = """
        INSERT INTO silver_pagamento (
            id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
            tipo_pagamento, valor
        ) VALUES (%s,%s,%s,%s,%s,%s)
    """
    total_inseridas, total_descartadas = 0, 0
    for bloco in ler_raw_em_blocos(conexao, "SELECT * FROM raw_pagamento"):
        linhas = []
        for linha in bloco:
            id_viagem = texto_ou_none(linha["id_viagem"])
            tipo_pagamento = texto_ou_none(linha["tipo_pagamento"])
            valor = converter_valor(linha["valor"])

            
            if id_viagem not in ids_validos or tipo_pagamento is None or valor is None or valor < 0:
                total_descartadas += 1
                continue

            linhas.append((
                id_viagem,
                texto_ou_none(linha["num_proposta"]),
                texto_ou_none(linha["nome_orgao_pagador"]),
                texto_ou_none(linha["nome_ug_pagadora"]),
                tipo_pagamento,
                valor,
            ))
        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total_inseridas += len(linhas)

    print(f"[OK] silver_pagamento: {total_inseridas} inseridas, {total_descartadas} descartadas.")

# -----------------------------------------------------------------------------

def transformar_passagem(conexao, ids_validos):
    sql_insert = """
        INSERT INTO silver_passagem (
            id_viagem, meio_transporte, pais_origem_ida, uf_origem_ida,
            cidade_origem_ida, pais_destino_ida, uf_destino_ida, cidade_destino_ida,
            valor_passagem, taxa_servico, data_emissao
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    total_inseridas, total_descartadas = 0, 0
    for bloco in ler_raw_em_blocos(conexao, "SELECT * FROM raw_passagem"):
        linhas = []
        for linha in bloco:
            id_viagem = texto_ou_none(linha["id_viagem"])
            valor_passagem = converter_valor(linha["valor_passagem"])
            taxa_servico = converter_valor(linha["taxa_servico"])

            if id_viagem not in ids_validos:
                total_descartadas += 1
                continue
            if valor_passagem is not None and valor_passagem < 0:
                total_descartadas += 1
                continue
            if taxa_servico is not None and taxa_servico < 0:
                total_descartadas += 1
                continue

            linhas.append((
                id_viagem,
                texto_ou_none(linha["meio_transporte"]),
                texto_ou_none(linha["pais_origem_ida"]),
                texto_ou_none(linha["uf_origem_ida"]),
                texto_ou_none(linha["cidade_origem_ida"]),
                texto_ou_none(linha["pais_destino_ida"]),
                texto_ou_none(linha["uf_destino_ida"]),
                texto_ou_none(linha["cidade_destino_ida"]),
                valor_passagem,
                taxa_servico,
                converter_data(linha["data_emissao"]),
            ))
        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total_inseridas += len(linhas)

    print(f"[OK] silver_passagem: {total_inseridas} inseridas, {total_descartadas} descartadas.")

# -----------------------------------------------------------------------------

def transformar_trecho(conexao, ids_validos):
    sql_insert = """
        INSERT INTO silver_trecho (
            id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade,
            destino_data, destino_uf, destino_cidade, meio_transporte, numero_diarias
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    total_inseridas, total_descartadas = 0, 0
    chaves_vistas = set()  # para respeitar o UNIQUE (id_viagem, sequencia_trecho)

    for bloco in ler_raw_em_blocos(conexao, "SELECT * FROM raw_trecho"):
        linhas = []
        for linha in bloco:
            id_viagem = texto_ou_none(linha["id_viagem"])
            seq_texto = texto_ou_none(linha["sequencia_trecho"])
            numero_diarias = converter_valor(linha["numero_diarias"])

            if id_viagem not in ids_validos or seq_texto is None:
                total_descartadas += 1
                continue
            try:
                sequencia_trecho = int(float(seq_texto))
            except ValueError:
                total_descartadas += 1
                continue

            chave = (id_viagem, sequencia_trecho)
            if chave in chaves_vistas:
                total_descartadas += 1
                continue
            if numero_diarias is not None and numero_diarias < 0:
                total_descartadas += 1
                continue
            chaves_vistas.add(chave)

            linhas.append((
                id_viagem,
                sequencia_trecho,
                converter_data(linha["origem_data"]),
                texto_ou_none(linha["origem_uf"]),
                texto_ou_none(linha["origem_cidade"]),
                converter_data(linha["destino_data"]),
                texto_ou_none(linha["destino_uf"]),
                texto_ou_none(linha["destino_cidade"]),
                texto_ou_none(linha["meio_transporte"]),
                numero_diarias,
            ))
        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total_inseridas += len(linhas)

    print(f"[OK] silver_trecho: {total_inseridas} inseridas, {total_descartadas} descartadas.")

# -----------------------------------------------------------------------------

def limpar_tabelas_silver(conexao):
    
    banco.executar(conexao, "SET FOREIGN_KEY_CHECKS = 0;")
    for tabela in ("silver_trecho", "silver_passagem", "silver_pagamento", "silver_viagem"):
        banco.executar(conexao, f"TRUNCATE TABLE {tabela};")
    banco.executar(conexao, "SET FOREIGN_KEY_CHECKS = 1;")

# -----------------------------------------------------------------------------

def main():
    print("=== FASE 2: Transformacao RAW -> SILVER ===")
    try:
        conexao = banco.conectar()
    except RuntimeError as erro:
        print(f"ERRO: {erro}")
        sys.exit(1)

    try:
        limpar_tabelas_silver(conexao)
        
        ids_validos = transformar_viagem(conexao)
        transformar_pagamento(conexao, ids_validos)
        transformar_passagem(conexao, ids_validos)
        transformar_trecho(conexao, ids_validos)
        print("=== FASE 2 concluida com sucesso. ===")
    except Exception as erro:
        print(f"ERRO durante a transformacao: {erro}")
        sys.exit(1)
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
