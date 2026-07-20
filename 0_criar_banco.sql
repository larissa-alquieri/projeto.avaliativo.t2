-- =============================================================================
-- 0_criar_banco.sql
-- Cria o banco "transparencia" e as 8 tabelas (4 Raw + 4 Silver).
-- Requer MySQL 8.0.16+ (necessario para as constraints CHECK serem aplicadas).
-- Execute este arquivo ANTES de rodar 1_extrair.py.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS transparencia
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE transparencia;

-- =============================================================================
-- CAMADA RAW
-- Copia fiel do CSV: todas as colunas em VARCHAR, sem PK/FK/constraint.
-- A ordem das colunas abaixo segue a ordem das colunas no CSV oficial do
-- Portal da Transparencia (Viagens a Servico). Se ao abrir o CSV voce notar
-- que a ordem/quantidade de colunas e diferente, ajuste aqui E na lista
-- COLUNAS_RAW de cada arquivo dentro de 1_extrair.py.
-- =============================================================================

DROP TABLE IF EXISTS raw_trecho;
DROP TABLE IF EXISTS raw_passagem;
DROP TABLE IF EXISTS raw_pagamento;
DROP TABLE IF EXISTS raw_viagem;

CREATE TABLE raw_viagem (
    id_viagem               VARCHAR(20),
    num_proposta            VARCHAR(20),
    situacao                VARCHAR(50),
    viagem_urgente          VARCHAR(5),
    justificativa_urgencia  VARCHAR(2000),
    cod_orgao_superior      VARCHAR(20),
    nome_orgao_superior     VARCHAR(500),
    cod_orgao_solicitante   VARCHAR(20),
    nome_orgao_solicitante  VARCHAR(500),
    cpf_viajante            VARCHAR(20),
    nome_viajante           VARCHAR(500),
    cargo                   VARCHAR(500),
    funcao                  VARCHAR(500),
    descricao_funcao        VARCHAR(500),
    data_inicio             VARCHAR(20),
    data_fim                VARCHAR(20),
    destinos                VARCHAR(4000),
    motivo                  VARCHAR(4000),
    valor_diarias           VARCHAR(20),
    valor_passagens         VARCHAR(20),
    valor_devolucao         VARCHAR(20),
    valor_outros_gastos     VARCHAR(20)
);

CREATE TABLE raw_pagamento (
    id_viagem            VARCHAR(20),
    num_proposta         VARCHAR(20),
    cod_orgao_superior   VARCHAR(20),
    nome_orgao_superior  VARCHAR(500),
    cod_orgao_pagador    VARCHAR(20),
    nome_orgao_pagador   VARCHAR(500),
    cod_ug_pagadora      VARCHAR(20),
    nome_ug_pagadora     VARCHAR(500),
    tipo_pagamento       VARCHAR(50),
    valor                VARCHAR(20)
);

CREATE TABLE raw_passagem (
    id_viagem            VARCHAR(20),
    num_proposta         VARCHAR(20),
    meio_transporte      VARCHAR(50),
    pais_origem_ida      VARCHAR(60),
    uf_origem_ida        VARCHAR(40),
    cidade_origem_ida    VARCHAR(80),
    pais_destino_ida     VARCHAR(60),
    uf_destino_ida       VARCHAR(40),
    cidade_destino_ida   VARCHAR(80),
    pais_origem_volta    VARCHAR(60),
    uf_origem_volta      VARCHAR(40),
    cidade_origem_volta  VARCHAR(80),
    pais_destino_volta   VARCHAR(60),
    uf_destino_volta     VARCHAR(40),
    cidade_destino_volta VARCHAR(80),
    valor_passagem       VARCHAR(20),
    taxa_servico         VARCHAR(20),
    data_emissao         VARCHAR(20),
    hora_emissao         VARCHAR(20)
);

CREATE TABLE raw_trecho (
    id_viagem         VARCHAR(20),
    num_proposta      VARCHAR(20),
    sequencia_trecho  VARCHAR(10),
    origem_data       VARCHAR(20),
    origem_pais       VARCHAR(60),
    origem_uf         VARCHAR(40),
    origem_cidade     VARCHAR(80),
    destino_data      VARCHAR(20),
    destino_pais      VARCHAR(60),
    destino_uf        VARCHAR(40),
    destino_cidade    VARCHAR(80),
    meio_transporte   VARCHAR(50),
    numero_diarias    VARCHAR(20),
    missao            VARCHAR(10)
);

-- =============================================================================
-- CAMADA SILVER
-- Dados limpos e tipados, com PK, FK e constraints (NOT NULL, CHECK, UNIQUE)
-- declaradas dentro do CREATE TABLE, conforme o dicionario de dados do desafio.
-- =============================================================================

DROP TABLE IF EXISTS silver_trecho;
DROP TABLE IF EXISTS silver_passagem;
DROP TABLE IF EXISTS silver_pagamento;
DROP TABLE IF EXISTS silver_viagem;

CREATE TABLE silver_viagem (
    id_viagem           VARCHAR(20)    NOT NULL,
    num_proposta        VARCHAR(20),
    situacao            VARCHAR(50),
    viagem_urgente      VARCHAR(5),
    cod_orgao_superior  VARCHAR(20),
    nome_orgao_superior VARCHAR(255)   NOT NULL,               -- constraint extra 1
    nome_viajante       VARCHAR(255),
    cargo               VARCHAR(255),
    data_inicio         DATE,
    data_fim            DATE,
    destinos            VARCHAR(4000),
    motivo              VARCHAR(4000),
    valor_diarias       DECIMAL(10,2)  CHECK (valor_diarias >= 0),   -- constraint extra 2
    valor_passagens     DECIMAL(10,2),
    valor_devolucao     DECIMAL(10,2),
    valor_outros_gastos DECIMAL(10,2),
    valor_total         DECIMAL(12,2),
    duracao_dias        INT,
    PRIMARY KEY (id_viagem)
);

CREATE TABLE silver_pagamento (
    id_pagamento        INT AUTO_INCREMENT,
    id_viagem           VARCHAR(20)   NOT NULL,
    num_proposta        VARCHAR(20),
    nome_orgao_pagador   VARCHAR(255),
    nome_ug_pagadora     VARCHAR(255),
    tipo_pagamento       VARCHAR(50)  NOT NULL,                       -- constraint extra 1
    valor                DECIMAL(10,2) CHECK (valor >= 0),            -- constraint extra 2
    PRIMARY KEY (id_pagamento),
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem)
);

CREATE TABLE silver_passagem (
    id_passagem         INT AUTO_INCREMENT,
    id_viagem           VARCHAR(20)   NOT NULL,
    meio_transporte     VARCHAR(50),
    pais_origem_ida     VARCHAR(60),
    uf_origem_ida       VARCHAR(40),
    cidade_origem_ida   VARCHAR(80),
    pais_destino_ida    VARCHAR(60),
    uf_destino_ida      VARCHAR(40),
    cidade_destino_ida  VARCHAR(80),
    valor_passagem      DECIMAL(10,2) CHECK (valor_passagem >= 0),    -- constraint extra 1
    taxa_servico        DECIMAL(10,2) CHECK (taxa_servico >= 0),      -- constraint extra 2
    data_emissao        DATE,
    PRIMARY KEY (id_passagem),
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem)
);

CREATE TABLE silver_trecho (
    id_trecho         INT AUTO_INCREMENT,
    id_viagem         VARCHAR(20)   NOT NULL,
    sequencia_trecho  INT,
    origem_data       DATE,
    origem_uf         VARCHAR(40),
    origem_cidade     VARCHAR(80),
    destino_data      DATE,
    destino_uf        VARCHAR(40),
    destino_cidade    VARCHAR(80),
    meio_transporte   VARCHAR(50),
    numero_diarias    DECIMAL(10,2) CHECK (numero_diarias >= 0),      -- constraint extra 1
    PRIMARY KEY (id_trecho),
    UNIQUE (id_viagem, sequencia_trecho),                              -- constraint extra 2
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem)
);
