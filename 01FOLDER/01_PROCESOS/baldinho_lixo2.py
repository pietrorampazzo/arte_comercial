# Script personalizado para oportunidades específicas
import pandas as pd
import json

# Carregar dados baixados
with open('downloads/licitacao_98428705900032025_latest.json', 'r') as f:
    dados = json.load(f)

# Análise rápida
if dados['licitacao']['_embedded']['licitacoes']:
    lic = dados['licitacao']['_embedded']['licitacoes'][0]
    print(f"Modalidade: {lic['modalidade_licitacao']}")
    print(f"Valor estimado: R$ {lic.get('valor_estimado', 'N/A')}")
    print(f"Situação: {lic['situacao_licitacao']}")