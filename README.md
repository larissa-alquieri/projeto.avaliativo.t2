# Objetivo: Construir, do zero, um pipeline de dados preservando o histórico original, limpar a estrutura e transformar os dados brutos em métricas e gráficos claros

## Problemas que o Projeto Resolve:
Os dados de Viagens a Serviço do Governo Federal são publicados no Portal da
Transparência em formato bruto (CSV, texto sem tipagem, sem integridade
referencial). Este projeto constrói um pipeline de dados, seguindo a Arquitetura Medallion (Raw → Silver → Gold).

## Técnicas e Tecnologias Utilizadas:
- **Python** (pandas, mysql-connector-python, gdown) para extração e transformação
- **MySQL 8** para armazenamento (camadas Raw, Silver e Gold)
- **Jupyter Notebook** + matplotlib para análise e visualização (camada Gold)
- **Arquitetura Medallion**: Raw (cópia fiel), Silver (dados tipados e íntegros),
  Gold (métricas agregadas para negócio)
- **Git/GitHub** para versionamento

## Melhorias Futuras:
- Ampliar o período analisado para mais anos de dados.
- Dividir as viagens de longa duração das curtas, para tornar os custos médios de maneira facilitada para comparação.

## Conclusões:
A análise dos dados de Viagens a Serviço revela um padrão, onde o custo e o volume de viagens não são distribuídos de forma uniforme entre órgãos, destinos ou deslocamento, mas se concentram em alguns locais mais recorrentes.

O Ministério da Justiça e Segurança Pública lidera o custo total, superando consideravelmente o Ministério da Defesa. Esse resultado é condiz com as funções de cada setor, onde o da Justiça necessita maiores deslocamentos pois existem nas principais cidades brasileiras, já os outros ministérios são mais concentrados em Brasília e seus a redores dispensando maiores gastos.

Os dados abrangem somente 6 meses de movimentações assim limitando as análises mais amplas 
