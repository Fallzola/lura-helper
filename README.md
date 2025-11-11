# Bot do Plurall 🤖

Este é um bot automatizado que abre o site do Plurall e aguarda o usuário fazer login, confirmando quando o processo for concluído.

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Google Chrome instalado
- Conexão com a internet

## 🚀 Instalação

1. **Clone ou baixe os arquivos para uma pasta**

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Baixe o ChromeDriver:**
   - Acesse: https://chromedriver.chromium.org/
   - Baixe a versão compatível com seu Chrome
   - Extraia o arquivo e coloque o `chromedriver.exe` na mesma pasta do projeto
   - **OU** adicione o ChromeDriver ao PATH do sistema

## 🎯 Como usar

1. **Execute o script:**
   ```bash
   python plurall.py
   ```

2. **O programa irá:**
   - Abrir o Google Chrome automaticamente
   - Navegar para https://login.plurall.net/
   - Aguardar você fazer login manualmente
   - Detectar automaticamente quando o login for concluído
   - Confirmar o sucesso no terminal
   - Fechar o navegador e finalizar

## ⚠️ Observações importantes

- **Não feche o navegador** enquanto o programa estiver rodando
- Faça o login normalmente como você faria manualmente
- O programa detecta automaticamente quando você está logado
- Se a detecção automática falhar, você pode pressionar Enter para continuar
- Para interromper o programa, use `Ctrl+C` no terminal

## 🔧 Solução de problemas

**Erro "ChromeDriver não encontrado":**
- Certifique-se de que o ChromeDriver está na mesma pasta do projeto
- Ou adicione o ChromeDriver ao PATH do sistema

**Erro "Chrome não encontrado":**
- Certifique-se de que o Google Chrome está instalado
- Verifique se o caminho do Chrome está correto

**Problemas de detecção de login:**
- O programa tenta detectar automaticamente, mas se falhar, você pode pressionar Enter para continuar

## 📝 Funcionalidades

- ✅ Abertura automática do navegador
- ✅ Navegação para o site do Plurall
- ✅ Detecção automática de login
- ✅ Confirmação no terminal
- ✅ Fechamento automático do navegador
- ✅ Tratamento de erros
- ✅ Interface amigável com emojis

## 🎨 Personalização

Você pode modificar o arquivo `plurall.py` para:
- Alterar o tempo de espera (padrão: 5 minutos)
- Modificar os seletores CSS para detecção de login
- Adicionar mais funcionalidades
- Personalizar as mensagens do terminal

