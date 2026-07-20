# Objetivo: Construir, do zero, um pipeline de dados preservando o histórico original, limpar a estrutura e transformar os dados brutos em métricas e gráficos claros

## 1. Problema que o projeto resolve
Os dados de Viagens a Serviço do Governo Federal são publicados no Portal da
Transparência em formato bruto (CSV, texto sem tipagem, sem integridade
referencial). Este projeto constrói um pipeline de dados, seguindo a Arquitetura Medallion (Raw → Silver → Gold).

## 2. Técnicas e tecnologias utilizadas
- **Python** (pandas, mysql-connector-python, gdown) para extração e transformação
- **MySQL 8** para armazenamento (camadas Raw, Silver e Gold)
- **Jupyter Notebook** + matplotlib para análise e visualização (camada Gold)
- **Arquitetura Medallion**: Raw (cópia fiel), Silver (dados tipados e íntegros),
  Gold (métricas agregadas para negócio)
- **Git/GitHub** para versionamento

