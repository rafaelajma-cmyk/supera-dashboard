# 📊 Dashboard de Pedidos – Streamlit

Este projeto apresenta um **dashboard interativo** desenvolvido em **Streamlit** com base no relatório `Relatório de Status de Pedido Copia.xlsx`.

## 🚀 Como visualizar online (sem instalar nada)

1. Faça login no [Streamlit Cloud](https://streamlit.io/cloud)
2. Clique em **New app**
3. Selecione este repositório
4. No campo **Main file path**, digite:
   ```
   streamlit_dashboard.py
   ```
5. Clique em **Deploy**

✅ O dashboard será aberto no navegador automaticamente.

---

## 💾 Arquivos incluídos
- `streamlit_dashboard.py`: código principal do app
- `Relatório de Status de Pedido Copia.xlsx`: base de dados
- `requirements.txt`: dependências do projeto

---

## ⚙️ Dependências
O Streamlit Cloud instala automaticamente as bibliotecas listadas em `requirements.txt`:

```
streamlit
pandas
plotly
openpyxl
```

---

## 📈 Funcionalidades
- Filtros interativos (mês, vendedor, status, cliente, etc.)
- Gráficos de:
  - Evolução mensal de faturamento
  - Distribuição por status de pedido
  - Performance por vendedor
  - Top 10 clientes
  - Políticas comerciais e condições de pagamento
- Tabelas dinâmicas e análises detalhadas

---

## 🧠 Autor
Desenvolvido por *Rafaela Martins* com auxílio do ChatGPT (GPT-5).
