import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Configurações ---
NOME_ARQUIVO_ENTRADA = 'raw2.txt'
NOME_ARQUIVO_SAIDA = 'liso.txt'
# Se o chromedriver.exe estiver na mesma pasta, o caminho é só o nome do arquivo.
# --- INICIALIZAÇÃO SIMPLIFICADA ---
print("Iniciando o bot...")
# Não precisamos mais do Service ou do caminho do driver
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options) # O Selenium vai gerenciar o driver automaticamente
wait = WebDriverWait(driver, 20)
# --- FIM DA INICIALIZAÇÃO ---
# --- Etapa de Login Manual ---
driver.get("https://login.plurall.net/")
print("\n" + "="*50)
print(">>> AÇÃO NECESSÁRIA <<<")
print("Uma janela do Chrome foi aberta. Por favor, faça o login na sua conta Plurall.")
input("Após o login ser concluído com sucesso, volte aqui e pressione ENTER para continuar...")
print("="*50 + "\n")
print("Login confirmado. Iniciando a extração dos links...")

# --- Leitura dos links do arquivo de entrada ---
try:
    with open(NOME_ARQUIVO_ENTRADA, 'r') as f:
        tarefa_urls = [line.strip() for line in f if line.strip()]
    if not tarefa_urls:
        print(f"Erro: O arquivo '{NOME_ARQUIVO_ENTRADA}' está vazio.")
        driver.quit()
        exit()
    print(f"Encontrados {len(tarefa_urls)} links de tarefas para processar.")
except FileNotFoundError:
    print(f"Erro: Arquivo de entrada '{NOME_ARQUIVO_ENTRADA}' não encontrado!")
    print("Certifique-se de que o arquivo existe e está na mesma pasta do script.")
    driver.quit()
    exit()

# --- Loop principal para extrair os links dos exercícios ---
all_exercise_links = []
# Seletor CSS para o container dos exercícios. Usamos '^=' para buscar uma classe que COMEÇA com o texto.
container_selector = 'div[class^="Exercises-module_exercises-holder__"]'

for index, url in enumerate(tarefa_urls):
    print(f"\n[{index + 1}/{len(tarefa_urls)}] Processando tarefa: {url}")
    driver.get(url)
    
    links_encontrados = []
    tentativas = 0
    
    # Loop de tentativas para garantir que os dados carreguem
    while not links_encontrados and tentativas < 5: # Tenta até 5 vezes por link
        try:
            # 1. Espera o container principal dos exercícios aparecer na página
            print("Esperando o container dos exercícios carregar...")
            container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, container_selector)))
            
            # 2. Dentro do container, busca todos os links que contém "/exercicio/"
            # Usamos um pequeno delay para garantir que os elementos filhos renderizem
            time.sleep(2) 
            links = container.find_elements(By.CSS_SELECTOR, 'a[href*="/exercicio/"]')
            
            if not links:
                raise TimeoutException # Força uma nova tentativa se o container estiver vazio

            # 3. Extrai o atributo 'href' de cada link encontrado
            for link_element in links:
                href = link_element.get_attribute('href')
                if href and href not in all_exercise_links:
                    links_encontrados.append(href)
                    all_exercise_links.append(href)
            
            print(f"Sucesso! Encontrados {len(links_encontrados)} links de exercícios nesta página.")

        except TimeoutException:
            tentativas += 1
            print(f"Container não carregou a tempo. Tentativa {tentativas}/5. Recarregando a página...")
            driver.refresh()
            time.sleep(3) # Espera um pouco após o refresh

# --- Salvando os resultados ---
if all_exercise_links:
    with open(NOME_ARQUIVO_SAIDA, 'w') as f:
        for link in all_exercise_links:
            f.write(link + '\n')
    print(f"\nExtração concluída! {len(all_exercise_links)} links de exercícios foram salvos em '{NOME_ARQUIVO_SAIDA}'.")
else:
    print("\nNenhum link de exercício foi encontrado.")

# --- Finalização ---
driver.quit()
print("Bot finalizado.")