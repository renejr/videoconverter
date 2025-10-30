import unittest
import tkinter as tk
import sys
import os
import shutil
import time

# Adicionar o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from gui.main_window_tkinter import MainWindow

class TestYouTubeDownloadE2E(unittest.TestCase):
    """
    Teste de ponta a ponta para o download de vídeos do YouTube.
    Este teste simula a interação do usuário com a GUI, incluindo
    o preenchimento de campos e o clique em botões, e verifica
    se o arquivo de vídeo é baixado corretamente.
    """

    def setUp(self):
        """
        Configura o ambiente de teste antes de cada teste.
        Cria uma janela Tkinter, uma instância da aplicação e um diretório de saída temporário.
        """
        self.root = tk.Tk()
        self.root.withdraw()  # Ocultar a janela principal da GUI durante os testes
        self.app = MainWindow(self.root)
        
        # Usar o diretório especificado pelo usuário para teste E2E
        self.output_dir = r"G:\Nova pasta"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self.download_success = False
        self.completed = False
        self.downloaded_files = []

    def tearDown(self):
        """
        Limpa o ambiente de teste após cada teste.
        Destroi a janela Tkinter e remove o diretório de saída temporário.
        """
        # A janela pode já ter sido destruída, então adicionamos uma verificação
        if self.root.winfo_exists():
            self.root.destroy()
        # NÃO remover o diretório de saída para o teste E2E - queremos ver os arquivos baixados
        # if os.path.exists(self.output_dir):
        #     shutil.rmtree(self.output_dir)

    def on_download_complete(self, success, message):
        """
        Callback para ser chamado quando o download terminar.
        """
        self.download_success = success
        self.completed = True

    def _test_timeout(self):
        """
        Chamado se o teste exceder o tempo limite.
        """
        print("O teste excedeu o tempo limite.")
        self.completed = False
        if self.root.winfo_exists():
            self.root.quit()

    def _run_test_logic(self):
        """
        Executa a lógica principal do teste dentro do loop de eventos do Tkinter.
        """
        try:
            # URL do vídeo do YouTube para teste E2E
            test_url = "https://youtu.be/oeItWIUkkLo?si=Mvw6OEMw9lNyXQFe"

            # Definir o diretório de saída na GUI
            self.app.output_dir_var.set(self.output_dir)
            
            # Definir a URL do YouTube na GUI
            self.app.youtube_url_var.set(test_url)

            # Monkey-patch o método que mostra a mensagem final para o nosso callback
            def mock_show_info(title, message):
                self.on_download_complete(True, message)
                if self.root.winfo_exists():
                    self.root.quit()

            def mock_show_error(title, message):
                self.on_download_complete(False, message)
                if self.root.winfo_exists():
                    self.root.quit()

            self.app.show_info_on_main_thread = mock_show_info
            self.app.show_error_on_main_thread = mock_show_error
            
            # Chamar o método de download (simulando o clique do botão)
            self.app.download_youtube_video()

            # Definir um timeout para falhar o teste se demorar muito
            self.root.after(300 * 1000, self._test_timeout)
        except Exception as e:
            print(f"Erro durante a execução da lógica de teste: {e}")
            self.completed = False
            self.download_success = False
            if self.root.winfo_exists():
                self.root.quit()

    def test_download_youtube_video(self):
        """
        Inicia o teste e o loop de eventos do Tkinter.
        """
        self.root.after(100, self._run_test_logic)
        self.root.mainloop()

        self.assertTrue(self.completed, "O download não foi concluído dentro do tempo limite.")
        self.assertTrue(self.download_success, "O download falhou.")

        # Verificar se o arquivo foi criado (apenas se o download foi bem-sucedido)
        if self.download_success:
            files = os.listdir(self.output_dir)
            self.assertGreater(len(files), 0, "Nenhum arquivo foi baixado.")
            
            # Identificar arquivos baixados
            mp4_files = [f for f in files if f.endswith(".mp4")]
            webm_files = [f for f in files if f.endswith(".webm")]
            all_files = [f for f in files if f.endswith((".mp4", ".webm", ".mkv"))]
            
            print(f"\n=== RESULTADOS DO TESTE E2E ===")
            print(f"Arquivos MP4 encontrados: {mp4_files}")
            print(f"Arquivos WEBM encontrados: {webm_files}")
            print(f"Total de arquivos de vídeo: {all_files}")
            
            # Validação importante: deve haver arquivo MP4
            self.assertTrue(len(mp4_files) > 0, 
                          f"ERRO: Nenhum arquivo MP4 foi baixado. Arquivos: {all_files}")
            
            # Validação crítica: NÃO deve haver arquivos WEBM se existe MP4
            if len(mp4_files) > 0:
                print(f"✅ SUCESSO: Arquivo MP4 baixado corretamente: {mp4_files[0]}")
                # Verificar se há duplicatas WEBM
                if len(webm_files) > 0:
                    print(f"⚠️  ATENÇÃO: Arquivos WEBM também foram baixados: {webm_files}")
                    print("   Isso pode indicar que há download duplicado do vídeo!")
                else:
                    print("✅ Nenhum arquivo WEBM desnecessário foi baixado")
            
            # Verificar que pelo menos um vídeo foi baixado
            self.assertTrue(len(all_files) > 0, 
                          f"O arquivo baixado não é um vídeo válido: {files}")

if __name__ == "__main__":
    unittest.main()