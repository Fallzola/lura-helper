from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import sys
import random
import re
import requests

def carregar_links():
    """Carrega os links do arquivo links_de_exercicios.txt"""
    try:
        with open('links_de_exercicios.txt', 'r', encoding='utf-8') as arquivo:
            links = [linha.strip() for linha in arquivo if linha.strip()]
        return links
    except FileNotFoundError:
        print("❌ Arquivo 'links_de_exercicios.txt' não encontrado!")
        return []
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {str(e)}")
        return []

def main():
    """Função principal do bot"""
    # TIMER: Inicia contagem de tempo total
    import time
    tempo_inicio = time.time()
    print("🚀 Iniciando bot do Plurall...")
    print(f"⏰ Início: {time.strftime('%H:%M:%S', time.localtime(tempo_inicio))}")
    
    # Configurar o Chrome para máxima velocidade
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # Otimizações de velocidade
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript-harmony-shipping")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # Inicializar o driver
    try:
        print("🔧 Inicializando Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Chrome inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar Chrome: {str(e)}")
        print("\n💡 SOLUÇÕES:")
        print("   1. Certifique-se de que o Google Chrome está instalado")
        print("   2. Baixe o ChromeDriver manualmente de: https://chromedriver.chromium.org/")
        print("   3. Coloque o ChromeDriver na mesma pasta do script ou no PATH do sistema")
        print("   4. Ou execute: pip install --upgrade selenium")
        return
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        # Abrir o Plurall
        print("🌐 Abrindo Plurall...")
        driver.get("https://login.plurall.net/")
        
        # Aguardar o usuário fazer login
        print("⏳ Aguardando login do usuário...")
        wait = WebDriverWait(driver, 300)  # 5 minutos para login
        
        # Aguardar até que a URL mude (indicando login bem-sucedido)
        wait.until(lambda d: "login.plurall.net" not in d.current_url)
        
        print("✅ Login detectado! Usuário logado com sucesso.")
        
        # Carregar os links dos exercícios
        links = carregar_links()
        total_links = len(links)
        print(f"📚 Carregados {total_links} links de exercícios")
        
        # Lista para armazenar questões que falharam
        questoes_falharam = []
        
        # PRIMEIRA PASSADA: Processar todas as questões com detecção ultra-rápida
        print("\n🔄 INICIANDO PRIMEIRA PASSADA...")
        for i, link in enumerate(links, 1):
            # TIMER: Inicia contagem de tempo para cada questão
            tempo_questao_inicio = time.time()
            print(f"\n📝 Questão {i}/{total_links}")
            print(f"🔗 Link: {link}")
            print(f"⏱️  Início da questão: {time.strftime('%H:%M:%S', time.localtime(tempo_questao_inicio))}")
            
            try:
                # Navegar para o link
                driver.get(link)
                
                # Detecção ULTRA-RÁPIDA: tenta detectar imediatamente
                resultado = analisar_questao_ultra_rapido(driver)
                
                # Se não conseguiu detectar, aguarda carregamento mínimo
                if resultado == "desconhecido":
                    print("⚠️  Detecção imediata falhou, aguardando carregamento mínimo...")
                    resultado = aguardar_carregamento_minimo(driver)
                
                # Se ainda não conseguiu detectar, tenta mais uma vez com carregamento completo
                if resultado == "desconhecido":
                    print("⚠️  Carregamento mínimo falhou, tentando carregamento completo...")
                    aguardar_carregamento_completo(driver)
                    resultado = analisar_questao_ultra_rapido(driver)
                
                # Se ainda não conseguiu detectar, pular a questão
                if resultado == "desconhecido":
                    print("❌ Questão não identificada mesmo após todas as tentativas - PULANDO")
                    continue
                
                # Processar a questão
                sucesso = processar_questao_otimizado(driver, i, total_links)
                
                if not sucesso:
                    questoes_falharam.append((i, link))
                    print(f"❌ Questão {i} falhou - será retentada depois")
                
            except Exception as e:
                print(f"❌ Erro ao processar questão {i}: {str(e)}")
                questoes_falharam.append((i, link))
                continue
            
            # TIMER: Finaliza contagem de tempo para cada questão
            tempo_questao_fim = time.time()
            tempo_questao_total = tempo_questao_fim - tempo_questao_inicio
            print(f"⏱️  Questão {i} concluída em: {tempo_questao_total:.1f}s")
        
        # SEGUNDA PASSADA: Retentar questões que falharam
        if questoes_falharam:
            print(f"\n🔄 INICIANDO SEGUNDA PASSADA - {len(questoes_falharam)} questões para retentar...")
            
            for i, (indice_original, link) in enumerate(questoes_falharam, 1):
                # TIMER: Inicia contagem de tempo para cada retentativa
                tempo_retentativa_inicio = time.time()
                print(f"\n🔄 Retentando questão {indice_original} ({i}/{len(questoes_falharam)})")
                print(f"🔗 Link: {link}")
                print(f"⏱️  Início da retentativa: {time.strftime('%H:%M:%S', time.localtime(tempo_retentativa_inicio))}")
                
                try:
                    # Navegar para o link
                    driver.get(link)
                    
                    # Aguardar carregamento completo para questões que falharam
                    aguardar_carregamento_completo(driver)
                    
                    # Processar a questão
                    sucesso = processar_questao_otimizado(driver, indice_original, total_links)
                    
                    if sucesso:
                        print(f"✅ Questão {indice_original} resolvida na segunda tentativa!")
                    else:
                        print(f"❌ Questão {indice_original} falhou novamente")
                        
                except Exception as e:
                    print(f"❌ Erro ao retentar questão {indice_original}: {str(e)}")
                    continue
                
                # TIMER: Finaliza contagem de tempo para cada retentativa
                tempo_retentativa_fim = time.time()
                tempo_retentativa_total = tempo_retentativa_fim - tempo_retentativa_inicio
                print(f"⏱️  Retentativa da questão {indice_original} concluída em: {tempo_retentativa_total:.1f}s")
        
        print("\n🎉 Processamento concluído!")
        
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
    
    finally:
        # TIMER: Calcula tempo total de execução
        tempo_fim = time.time()
        tempo_total = tempo_fim - tempo_inicio
        
        # Converte para formato legível
        horas = int(tempo_total // 3600)
        minutos = int((tempo_total % 3600) // 60)
        segundos = int(tempo_total % 60)
        
        print(f"\n⏱️  TIMER TOTAL DE EXECUÇÃO:")
        print(f"⏰ Início: {time.strftime('%H:%M:%S', time.localtime(tempo_inicio))}")
        print(f"⏰ Fim: {time.strftime('%H:%M:%S', time.localtime(tempo_fim))}")
        print(f"⏱️  Duração total: {horas:02d}:{minutos:02d}:{segundos:02d}")
        print(f"⏱️  Segundos totais: {tempo_total:.1f}s")
        
        # Aguardar um pouco antes de fechar
        driver.quit()
        print("👋 Bot finalizado!")

def aguardar_carregamento_minimo(driver):
    """Aguarda apenas o carregamento mínimo necessário para detectar a questão"""
    print("⚡ Aguardando carregamento mínimo...")
    
    try:
        # Aguarda apenas 3 segundos para elementos básicos (reduzido de 5 para 3)
        wait = WebDriverWait(driver, 3)
        
        # Aguarda o DOM estar pronto
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        # Aguarda mais 1 segundo para garantir que elementos carregaram
        import time
        time.sleep(1)
        
        # Tenta detectar rapidamente
        return analisar_questao_ultra_rapido(driver)
        
    except Exception as e:
        print(f"⚠️  Erro ao aguardar carregamento mínimo: {str(e)}")
        return "desconhecido"

def aguardar_carregamento_completo(driver):
    """Aguarda a página carregar completamente para questões que falharam"""
    print("⏳ Aguardando carregamento completo...")
    
    try:
        # Aguarda até 15 segundos para a página carregar (reduzido de 20 para 15)
        wait = WebDriverWait(driver, 15)
        
        # Aguarda o DOM estar pronto
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        # Aguarda mais 2 segundos para garantir que tudo carregou
        import time
        time.sleep(2)
        
        # Aguarda pelo menos um dos elementos principais aparecer
        elementos_principais = [
            "li.option",
            '[data-test-id="response-textarea"]',
            '[data-test-id="input-image-id-button"]',
            '.Answer-module_answer-container__HR7MK.answer-container',
            '[class*="answer-container"]'
        ]
        
        elemento_encontrado = False
        for seletor in elementos_principais:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor)))
                print(f"✅ Elemento encontrado: {seletor}")
                elemento_encontrado = True
                break
            except:
                continue
        
        if not elemento_encontrado:
            print("⚠️  Nenhum elemento principal encontrado")
        
        print("✅ Página carregada completamente!")
        
    except Exception as e:
        print(f"⚠️  Erro ao aguardar carregamento: {str(e)}")

def analisar_questao_ultra_rapido(driver):
    """Analisa ULTRA-rapidamente o tipo de questão com retry inteligente"""
    max_tentativas = 5  # Máximo de 5 tentativas
    tentativa = 0
    
    while tentativa < max_tentativas:
        tentativa += 1
        
        try:
            # PRIMEIRO: Verificar se é questão de texto já respondida (alta prioridade)
            try:
                seletores_resposta = [
                    '.Answer-module_answer-container__HR7MK.answer-container',
                    '[class*="Answer-module_answer-container"]',
                    '[class*="answer-container"]',
                    '[class*="answer"][class*="container"]'
                ]
                
                for seletor in seletores_resposta:
                    try:
                        resposta = driver.find_element(By.CSS_SELECTOR, seletor)
                        if resposta:
                            return "texto_respondida"
                    except:
                        continue
            except:
                pass
            
            # SEGUNDO: Verificar se é questão de texto não respondida
            try:
                textarea = driver.find_element(By.CSS_SELECTOR, '[data-test-id="response-textarea"]')
                if textarea:
                    return "texto"
            except:
                pass
            
            # TERCEIRO: Verificar se é questão de múltipla escolha
            try:
                opcoes = driver.find_elements(By.CSS_SELECTOR, "li.option")
                if len(opcoes) >= 4:
                    # Verificar se já foi respondida
                    for opcao in opcoes:
                        try:
                            check = opcao.find_element(By.XPATH, './/*[@data-test-id="icon-Check"]')
                            if check:
                                return "multipla_escolha_respondida"
                        except:
                            continue
                    return "multipla_escolha"
            except:
                pass
            
            # QUARTO: Verificar se é questão de imagem
            try:
                imagem = driver.find_element(By.CSS_SELECTOR, '[data-test-id="input-image-id-button"]')
                if imagem:
                    return "imagem"
            except:
                pass
            
            # Se não conseguiu detectar nada nesta tentativa
            if tentativa < max_tentativas:
                print(f"⚠️  Tentativa {tentativa}/{max_tentativas} falhou, aguardando 1 segundo...")
                import time
                time.sleep(1)  # Espera apenas 1 segundo antes de tentar novamente
                continue
            
            # Se chegou aqui, não conseguiu detectar mesmo após todas as tentativas
            return "desconhecido"
            
        except Exception as e:
            print(f"⚠️  Erro na análise ultra-rápida (tentativa {tentativa}): {str(e)}")
            if tentativa < max_tentativas:
                import time
                time.sleep(1)  # Espera 1 segundo antes de tentar novamente
                continue
            return "desconhecido"

def responder_questao_texto_otimizado(driver):
    """Responde automaticamente uma questão de texto com máxima velocidade"""
    print("📝 Bot respondendo questão de texto...")
    
    try:
        # Encontra a textarea
        textarea = driver.find_element(By.CSS_SELECTOR, '[data-test-id="response-textarea"]')
        if not textarea:
            print("❌ Textarea não encontrada")
            return False
        
        # Gera pontos aleatórios (20 a 40 pontos)
        num_pontos = random.randint(20, 40)
        resposta = "." * num_pontos
        
        print(f"✍️  Escrevendo resposta: {num_pontos} pontos")
        
        # Limpa o campo e escreve a resposta
        textarea.clear()
        textarea.send_keys(resposta)
        
        # Encontra e clica no botão de enviar
        botao_enviar = driver.find_element(By.CSS_SELECTOR, 'button[type="button"][data-test-id="send-button"]')
        if not botao_enviar:
            print("❌ Botão de enviar não encontrado")
            return False
        
        print("📤 Enviando resposta...")
        botao_enviar.click()
        
        # Aguarda o popup de confirmação aparecer (wait baseado na web)
        wait = WebDriverWait(driver, 5)
        try:
            botao_confirmar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="button"][class*="css-sakhm0"]')))
            print("✅ Popup de confirmação encontrado, confirmando envio...")
            botao_confirmar.click()
        except:
            # Fallback: tenta encontrar por classe parcial
            try:
                botao_confirmar = driver.find_element(By.CSS_SELECTOR, 'button[class*="css-sakhm0"]')
                print("✅ Popup de confirmação encontrado (fallback), confirmando envio...")
                botao_confirmar.click()
            except:
                print("⚠️  Popup de confirmação não encontrado, tentando continuar...")
        
        # Aguarda a resposta ser processada (wait baseado na web)
        wait = WebDriverWait(driver, 10)
        try:
            # Aguarda até que a textarea desapareça ou apareça indicador de sucesso
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-test-id="response-textarea"]')) == 0 or 
                               len(d.find_elements(By.CSS_SELECTOR, '.Answer-module_answer-container__HR7MK.answer-container')) > 0)
            print("✅ Questão de texto respondida com sucesso!")
            return True
        except:
            print("⚠️  Timeout aguardando confirmação, mas assumindo sucesso")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao responder questão de texto: {str(e)}")
        return False

def responder_questao_multipla_via_clique_otimizado(driver):
    """Responde automaticamente uma questão de múltipla escolha via clique com máxima velocidade"""
    print("🤖 Bot respondendo questão de múltipla escolha via clique...")
    
    # Primeiro, conta quantas opções existem na página
    opcoes_totais = driver.find_elements(By.CSS_SELECTOR, "li.option")
    num_opcoes = len(opcoes_totais)
    print(f"📊 Questão com {num_opcoes} opções disponíveis")
    
    if num_opcoes == 0:
        print("❌ Nenhuma opção encontrada")
        return False
    
    # Loop infinito até encontrar a resposta correta
    tentativa = 0
    while True:
        tentativa += 1
        print(f"🔄 Tentativa {tentativa}")
        
        # PRIMEIRO: Verifica se já existe um ícone de check na página (questão já respondida)
        try:
            icon_check_existente = driver.find_elements(By.CSS_SELECTOR, 'li.option [data-test-id="icon-Check"]')
            if icon_check_existente:
                print("🎉 Questão já respondida corretamente! Ícone de check encontrado!")
                return True
        except:
            pass
        
        # SEGUNDO: Encontra todas as opções (sempre busca elementos frescos)
        opcoes = driver.find_elements(By.CSS_SELECTOR, "li.option span[data-test-id='option']")
        if not opcoes:
            print("❌ Nenhuma opção clicável encontrada")
            opcoes = driver.find_elements(By.CSS_SELECTOR, "li.option")
            if not opcoes:
                print("❌ Nenhuma opção encontrada")
                return False
        
        # TERCEIRO: Filtra opções que ainda não foram escolhidas
        opcoes_nao_escolhidas = []
        for i, opcao in enumerate(opcoes):
            try:
                # Usa índice para evitar stale element reference
                opcao_atual = driver.find_elements(By.CSS_SELECTOR, "li.option span[data-test-id='option']")[i]
                li_pai = opcao_atual.find_element(By.XPATH, "./ancestor::li[contains(@class, 'option')]")
                icon_check = li_pai.find_elements(By.CSS_SELECTOR, '[data-test-id="icon-Check"]')
                icon_cancel = li_pai.find_elements(By.CSS_SELECTOR, '[data-test-id="icon-Cancel"]')
            except:
                try:
                    # Fallback: busca por índice direto
                    opcoes_li = driver.find_elements(By.CSS_SELECTOR, "li.option")
                    if i < len(opcoes_li):
                        li_atual = opcoes_li[i]
                        icon_check = li_atual.find_elements(By.CSS_SELECTOR, '[data-test-id="icon-Check"]')
                        icon_cancel = li_atual.find_elements(By.CSS_SELECTOR, '[data-test-id="icon-Cancel"]')
                    else:
                        continue
                except:
                    continue
            
            if not icon_check and not icon_cancel:
                opcoes_nao_escolhidas.append(i)  # Armazena índice em vez do elemento
        
        if not opcoes_nao_escolhidas:
            print("✅ Todas as opções já foram testadas, mas nenhuma correta encontrada")
            return False
        
        # QUARTO: Escolhe a primeira opção não escolhida (por índice)
        indice_escolhido = opcoes_nao_escolhidas[0]
        print(f"🎯 Escolhendo opção {indice_escolhido + 1}...")
        
        try:
            # QUINTO: Busca o elemento fresco e clica
            print("👆 Clicando na opção...")
            
            # Busca elementos frescos para evitar stale reference
            opcoes_frescas = driver.find_elements(By.CSS_SELECTOR, "li.option span[data-test-id='option']")
            if not opcoes_frescas:
                opcoes_frescas = driver.find_elements(By.CSS_SELECTOR, "li.option")
            
            if indice_escolhido < len(opcoes_frescas):
                opcao_fresca = opcoes_frescas[indice_escolhido]
                opcao_fresca.click()
                print("✅ Opção clicada, aguardando resposta...")
            else:
                print("❌ Índice de opção inválido")
                continue
            
            # SEXTO: Aguarda resposta usando wait baseado na web
            wait = WebDriverWait(driver, 8)
            try:
                # Aguarda até que apareça ícone de check ou cancel
                wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, 'li.option [data-test-id="icon-Check"]')) > 0 or 
                                   len(d.find_elements(By.CSS_SELECTOR, 'li.option [data-test-id="icon-Cancel"]')) > 0)
                
                # SÉTIMO: Verifica se acertou (busca elementos frescos)
                try:
                    # Busca elementos frescos para verificação
                    opcoes_verificacao = driver.find_elements(By.CSS_SELECTOR, "li.option")
                    if indice_escolhido < len(opcoes_verificacao):
                        li_verificacao = opcoes_verificacao[indice_escolhido]
                        opcao_correta = li_verificacao.find_elements(By.CSS_SELECTOR, '[data-test-id="icon-Check"]')
                    else:
                        opcao_correta = driver.find_elements(By.CSS_SELECTOR, 'li.option [data-test-id="icon-Check"]')
                except:
                    opcao_correta = driver.find_elements(By.CSS_SELECTOR, 'li.option [data-test-id="icon-Check"]')
                    
                if opcao_correta:
                    print("🎉 Questão respondida corretamente!")
                    return True
                else:
                    print("❌ Opção incorreta, tentando próxima...")
                    continue
                    
            except:
                print("⚠️  Timeout aguardando resposta, tentando próxima opção...")
                continue
            
        except Exception as e:
            print(f"❌ Erro ao clicar na opção: {str(e)}")
            # Se for erro de stale element, aguarda um pouco e tenta novamente
            if "stale element" in str(e).lower():
                print("⚠️  Erro de elemento obsoleto, aguardando 2 segundos...")
                import time
                time.sleep(2)
            continue

def extrair_ids_da_url(url):
    """Extrai os IDs necessários da URL do exercício"""
    padrao = r'/material/(\d+)/aula/(\d+)/tarefa/(\d+)/exercicio/(\d+)/'
    match = re.search(padrao, url)
    
    if match:
        material_id = match.group(1)
        aula_id = match.group(2)
        tarefa_id = match.group(3)
        exercicio_id = match.group(4)
        return {
            'material_id': material_id,
            'aula_id': aula_id,
            'tarefa_id': tarefa_id,
            'exercicio_id': exercicio_id
        }
    return None

def obter_token_autorizacao(driver):
    """Extrai o token de autorização do navegador"""
    try:
        # Método 1: Procura por qualquer elemento que contenha o token Bearer
        scripts = driver.find_elements(By.TAG_NAME, "script")
        for script in scripts:
            script_content = script.get_attribute("innerHTML")
            if "Bearer" in script_content:
                match = re.search(r'Bearer\s+([a-f0-9]{32})', script_content)
                if match:
                    return match.group(1)
        
        # Método 2: Procura no HTML da página
        page_source = driver.page_source
        if "Bearer" in page_source:
            match = re.search(r'Bearer\s+([a-f0-9]{32})', page_source)
            if match:
                return match.group(1)
        
        # Método 3: Procura por padrões de token sem "Bearer"
        if "Bearer" in page_source:
            matches = re.findall(r'[a-f0-9]{32}', page_source)
            for match in matches:
                if len(match) == 32 and all(c in '0123456789abcdef' for c in match):
                    print(f"🔑 Token encontrado no HTML: {match[:8]}...")
                    return match
        
        # Método 4: Tenta extrair do localStorage
        token = driver.execute_script("return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token') || localStorage.getItem('token') || sessionStorage.getItem('token');")
        if token:
            print(f"🔑 Token encontrado no storage: {token[:8]}...")
            return token
            
        # Método 5: Tenta extrair dos cookies
        cookies = driver.get_cookies()
        for cookie in cookies:
            if 'auth' in cookie['name'].lower() or 'token' in cookie['name'].lower():
                print(f"🔑 Token encontrado nos cookies: {cookie['value'][:8]}...")
                return cookie['value']
        
        # Método 6: Procura por variáveis JavaScript
        js_vars = driver.execute_script("""
            return {
                'auth_token': window.auth_token || window.token || window.AUTH_TOKEN || window.TOKEN,
                'user_token': window.user_token || window.userToken || window.USER_TOKEN,
                'session_token': window.session_token || window.sessionToken || window.SESSION_TOKEN
            };
        """)
        
        for key, value in js_vars.items():
            if value and len(str(value)) >= 20:
                print(f"🔑 Token encontrado em variável JS {key}: {str(value)[:8]}...")
                return str(value)
                
    except Exception as e:
        print(f"⚠️  Erro ao extrair token: {str(e)}")
    
    print("❌ Token não encontrado por nenhum método")
    return None

def obter_client_id(driver):
    """Extrai o client ID do navegador"""
    try:
        # Método 1: Procura por elementos que contenham o client ID
        scripts = driver.find_elements(By.TAG_NAME, "script")
        for script in scripts:
            script_content = script.get_attribute("innerHTML")
            if "PLTR." in script_content:
                match = re.search(r'PLTR\.[a-f0-9-]+\.\d+', script_content)
                if match:
                    return match.group(0)
        
        # Método 2: Procura no HTML da página
        page_source = driver.page_source
        if "PLTR." in page_source:
            match = re.search(r'PLTR\.[a-f0-9-]+\.\d+', page_source)
            if match:
                return match.group(0)
        
        # Método 3: Procura em elementos específicos
        elements = driver.find_elements(By.CSS_SELECTOR, "[data-client-id], [client-id], .client-id")
        for element in elements:
            client_id = element.get_attribute("data-client-id") or element.get_attribute("client-id") or element.text
            if client_id and "PLTR." in client_id:
                return client_id
        
        # Método 4: Gera um client ID baseado no padrão observado
        print("⚠️  Client ID não encontrado, gerando um baseado no padrão...")
        import time
        timestamp = int(time.time() * 1000)
        random_hex = ''.join(random.choices('0123456789abcdef', k=32))
        generated_client_id = f"PLTR.{random_hex}.{timestamp}"
        print(f"🆔 Client ID gerado: {generated_client_id}")
        return generated_client_id
                    
    except Exception as e:
        print(f"⚠️  Erro ao extrair client ID: {str(e)}")
        # Fallback: gera um client ID
        import time
        timestamp = int(time.time() * 1000)
        random_hex = ''.join(random.choices('0123456789abcdef', k=32))
        generated_client_id = f"PLTR.{random_hex}.{timestamp}"
        print(f"🆔 Client ID gerado como fallback: {generated_client_id}")
        return generated_client_id

def responder_questao_via_api(url, token, client_id):
    """Responde uma questão usando a API do Plurall"""
    try:
        # Extrai os IDs da URL
        ids = extrair_ids_da_url(url)
        if not ids:
            print("❌ Não foi possível extrair IDs da URL")
            return False
        
        tarefa_id = ids['tarefa_id']
        exercicio_id = ids['exercicio_id']
        
        # Headers necessários
        headers = {
            'authority': 'api.plurall.net',
            'accept': 'application/json, text/plain, */*, vnd.plurall.api.v3+json',
            'accept-language': 'pt-BR,pt;q=0.9',
            'authorization': f'Bearer {token}',
            'client': client_id,
            'content-type': 'application/json',
            'origin': 'https://atividades.plurall.net',
            'referer': 'https://atividades.plurall.net/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Brave";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        # Opções de resposta baseadas no número de opções na página
        opcoes_disponiveis = ['a', 'b', 'c', 'd', 'e']
        
        # Verifica quantas opções existem na página atual
        opcoes_pagina = driver.find_elements(By.CSS_SELECTOR, "li.option")
        num_opcoes = len(opcoes_pagina)
        
        # Ajusta as opções baseado no número real de opções na página
        if num_opcoes == 4:
            opcoes = ['a', 'b', 'c', 'd']
            print(f"📊 Questão com {num_opcoes} opções (A, B, C, D)")
        elif num_opcoes == 3:
            opcoes = ['a', 'b', 'c']
            print(f"📊 Questão com {num_opcoes} opções (A, B, C)")
        elif num_opcoes == 2:
            opcoes = ['a', 'b']
            print(f"📊 Questão com {num_opcoes} opções (A, B)")
        else:
            opcoes = opcoes_disponiveis
            print(f"📊 Questão com {num_opcoes} opções (A, B, C, D, E)")
        
        for opcao in opcoes:
            print(f"🎲 Tentando opção: {opcao.upper()}")
            
            # Payload para a resposta
            payload = {"answer": opcao}
            
            # URL da API
            api_url = f"https://api.plurall.net/api/task_workflows/{tarefa_id}/subtasks/{exercicio_id}/answer"
            
            # Faz o request POST
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') == 'success':
                    status = data['data']['update_interface_data']['status']
                    user_answer = data['data']['update_interface_data']['user_answer']
                    attempts = data['data']['update_interface_data']['attempts_in_words']
                    
                    print(f"📡 Resposta enviada: {user_answer.upper()}")
                    print(f"📊 Status: {status}")
                    print(f"🔄 {attempts}")
                    
                    if status == 'correct':
                        print("🎉 Questão respondida corretamente!")
                        return True
                    elif status == 'wrong':
                        print("❌ Opção incorreta, tentando próxima...")
                        continue
                    elif status == 'completed' or status == 'finished':
                        print("✅ Questão marcada como completa/finalizada!")
                        return True
                    else:
                        print(f"⚠️  Status desconhecido: {status}")
                        if 'completed' in str(data).lower() or 'finished' in str(data).lower() or 'success' in str(data).lower():
                            print("✅ Indicadores de sucesso encontrados na resposta da API!")
                            return True
                        continue
                else:
                    print(f"❌ Erro na resposta da API: {data}")
                    continue
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                continue
        
        print("⚠️  Todas as opções foram testadas sem sucesso")
        return False
        
    except Exception as e:
        print(f"❌ Erro ao responder via API: {str(e)}")
        return False

def debug_autenticacao(driver):
    """Função de debug para identificar informações de autenticação"""
    print("🔍 Debug: Procurando informações de autenticação...")
    
    try:
        # Verifica se está na página de login
        if "login" in driver.current_url.lower():
            print("⚠️  Ainda na página de login. Faça login primeiro!")
            return False
        
        # Procura por tokens no HTML
        page_source = driver.page_source
        
        # Procura por padrões de token
        bearer_tokens = re.findall(r'Bearer\s+([a-f0-9]{32})', page_source)
        if bearer_tokens:
            print(f"🔑 Tokens Bearer encontrados: {len(bearer_tokens)}")
            for i, token in enumerate(bearer_tokens[:3]):
                print(f"   {i+1}. {token[:8]}...")
        
        # Procura por client IDs
        client_ids = re.findall(r'PLTR\.[a-f0-9-]+\.\d+', page_source)
        if client_ids:
            print(f"🆔 Client IDs encontrados: {len(client_ids)}")
            for i, client_id in enumerate(client_ids[:3]):
                print(f"   {i+1}. {client_id}")
        
        # Verifica localStorage e sessionStorage
        storage_data = driver.execute_script("""
            return {
                'localStorage': Object.keys(localStorage).filter(key => 
                    key.toLowerCase().includes('token') || 
                    key.toLowerCase().includes('auth') ||
                    key.toLowerCase().includes('client')
                ),
                'sessionStorage': Object.keys(sessionStorage).filter(key => 
                    key.toLowerCase().includes('token') || 
                    key.toLowerCase().includes('auth') ||
                    key.toLowerCase().includes('client')
                )
            };
        """)
        
        if storage_data['localStorage']:
            print(f"💾 Chaves no localStorage: {storage_data['localStorage']}")
        if storage_data['sessionStorage']:
            print(f"💾 Chaves no sessionStorage: {storage_data['sessionStorage']}")
        
        # Verifica cookies
        cookies = driver.get_cookies()
        auth_cookies = [c for c in cookies if 'auth' in c['name'].lower() or 'token' in c['name'].lower()]
        if auth_cookies:
            print(f"🍪 Cookies de autenticação: {len(auth_cookies)}")
            for cookie in auth_cookies[:3]:
                print(f"   {cookie['name']}: {cookie['value'][:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no debug: {str(e)}")
        return False

def processar_questao_otimizado(driver, i, total):
    """Processa uma questão específica com máxima otimização"""
    try:
        # Analisar a questão ultra-rapidamente
        resultado = analisar_questao_ultra_rapido(driver)
        
        # Se não conseguiu detectar, aguardar carregamento mínimo
        if resultado == "desconhecido":
            resultado = aguardar_carregamento_minimo(driver)
        
        # Se ainda não conseguiu detectar, retornar False
        if resultado == "desconhecido":
            print("❌ Questão não identificada")
            return False
        
        # Processar baseado no tipo de questão
        if resultado == "multipla_escolha":
            return processar_multipla_escolha_otimizado(driver, i, total)
        elif resultado == "texto":
            return processar_texto_otimizado(driver, i, total)
        elif resultado == "texto_respondida":
            print("✅ Questão de texto já respondida")
            return True
        elif resultado == "multipla_escolha_respondida":
            print("✅ Questão de múltipla escolha já respondida")
            return True
        elif resultado == "imagem":
            print("🖼️  Questão de imagem - pulando")
            return True
        else:
            print(f"❓ Tipo de questão desconhecido: {resultado}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar questão: {str(e)}")
        return False

def processar_multipla_escolha_otimizado(driver, i, total):
    """Processa uma questão de múltipla escolha com máxima otimização"""
    print(f"\n📝 Questão {i}/{total} - Múltipla Escolha")
    
    # Tenta responder via clique direto
    print("🎯 Tentando responder via clique direto...")
    sucesso_clique = responder_questao_multipla_via_clique_otimizado(driver)
    
    if sucesso_clique:
        # VERIFICAÇÃO RÁPIDA: Recarrega e confirma que foi respondida
        print("🔍 Verificando se a questão foi realmente respondida...")
        driver.refresh()
        aguardar_carregamento_minimo(driver)
        
        # Analisa novamente para confirmar
        resultado = analisar_questao_ultra_rapido(driver)
        if resultado == "multipla_escolha_respondida":
            print("✅ VERIFICAÇÃO: Questão confirmada como respondida via clique!")
            return True
        else:
            print("⚠️  VERIFICAÇÃO: Questão não foi respondida via clique, tentando via API...")
            
            # Se o clique falhou, tenta via API
            return tentar_api_como_fallback(driver, i, total)
    else:
        print("⚠️  Clique direto falhou, tentando via API...")
        return tentar_api_como_fallback(driver, i, total)

def tentar_api_como_fallback(driver, i, total):
    """Tenta responder via API como fallback"""
    # Obtém o token e client ID necessários
    token = obter_token_autorizacao(driver)
    client_id = obter_client_id(driver)
    
    if not token or not client_id:
        print("❌ Não foi possível obter credenciais de autenticação")
        print("🔍 Executando debug de autenticação...")
        debug_autenticacao(driver)
        return False
    
    print(f"🔑 Token obtido: {token[:8]}...")
    print(f"🆔 Client ID obtido: {client_id}")
    
    # Obtém a URL atual
    url_atual = driver.current_url
    
    # Responde via API
    sucesso = responder_questao_via_api(url_atual, token, client_id)
    
    if sucesso:
        # VERIFICAÇÃO RÁPIDA: Recarrega e confirma que foi respondida
        print("🔍 Verificando se a questão foi realmente respondida via API...")
        driver.refresh()
        aguardar_carregamento_minimo(driver)
        
        # Analisa novamente para confirmar
        resultado = analisar_questao_ultra_rapido(driver)
        if resultado == "multipla_escolha_respondida":
            print("✅ VERIFICAÇÃO: Questão confirmada como respondida via API!")
            return True
        else:
            print("⚠️  VERIFICAÇÃO: Questão não foi respondida via API")
            return False
    else:
        print("⚠️  Não foi possível responder a questão via API")
        return False

def processar_texto_otimizado(driver, i, total):
    """Processa uma questão de texto com máxima otimização"""
    print(f"\n📝 Questão {i}/{total} - Texto")
    
    # Tenta responder automaticamente
    print("📝 Bot respondendo questão de texto...")
    sucesso_texto = responder_questao_texto_otimizado(driver)
    
    if sucesso_texto:
        # VERIFICAÇÃO RÁPIDA: Recarrega e confirma que foi respondida
        print("🔍 Verificando se a questão de texto foi realmente respondida...")
        driver.refresh()
        aguardar_carregamento_minimo(driver)
        
        # Analisa novamente para confirmar
        resultado = analisar_questao_ultra_rapido(driver)
        if resultado == "texto_respondida":
            print("✅ VERIFICAÇÃO: Questão de texto confirmada como respondida!")
            return True
        else:
            print("⚠️  VERIFICAÇÃO: Questão de texto não foi respondida")
            return False
    else:
        print("⚠️  Não foi possível responder a questão de texto")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Programa interrompido pelo usuário.")
        sys.exit(0)
