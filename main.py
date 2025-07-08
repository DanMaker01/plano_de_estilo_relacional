import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import json
import os
import numpy as np

class PlanoAfetivo:
    def __init__(self, root):
        self.root = root
        self.root.title("Mapa de Estilo Relacional")

        self.frame_principal = tk.Frame(root)
        self.frame_principal.pack(fill=tk.BOTH, expand=True)

        self.frame_mapa = tk.Frame(self.frame_principal)
        self.frame_mapa.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.frame_direito = tk.Frame(self.frame_principal, width=250)
        self.frame_direito.pack(side=tk.RIGHT, fill=tk.Y)

        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_mapa)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.ax.axhline(0, color='black', linewidth=1)
        self.ax.axvline(0, color='black', linewidth=1)
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_xlabel("Gostar")
        self.ax.set_ylabel("Importância")

        self.ax.text(0.5, 0.5, "Quero manter por perto", ha='center', va='center', fontsize=10, color='green')
        self.ax.text(-0.5, 0.5, "Relações de validação", ha='center', va='center', fontsize=10, color='blue')
        self.ax.text(-0.5, -0.5, "Quero me afastar", ha='center', va='center', fontsize=10, color='red')
        self.ax.text(0.5, -0.5, "Relações de utilidade", ha='center', va='center', fontsize=10, color='orange')

        self.pontos = []  # Guarda TODOS os pontos em TODOS os tempos
        self.pontos_artist = []  # Artistas atuais no plot
        self.dragging_point = None

        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.lista = tk.Listbox(self.frame_direito, width=30)
        self.lista.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.botao_adicionar = tk.Button(self.frame_direito, text="Inserir ponto (tempo atual)", command=self.adicionar_ponto_manual)
        self.botao_adicionar.pack(pady=2)

        self.botao_deletar = tk.Button(self.frame_direito, text="Deletar ponto selecionado", command=self.deletar_ponto_selecionado)
        self.botao_deletar.pack(pady=2)

        self.botao_copiar = tk.Button(self.frame_direito, text="Copiar pontos tempo seguinte", command=self.copiar_pontos_para_tempo_seguinte)
        self.botao_copiar.pack(pady=2)

        self.botao_apagar_tempo_atual = tk.Button(self.frame_direito, text="Apagar todos pontos (tempo atual)", command=self.apagar_pontos_tempo_atual)
        self.botao_apagar_tempo_atual.pack(pady=2)  


        self.label_coord = tk.Label(self.frame_direito, text="Adicione tudo que você se relaciona\nex.: pessoas, animais, trabalho, etc...\n\n(Duplo clique para inserir/remover)\n(Arraste para mover)")
        self.label_coord.pack(pady=10)

        # Controle de tempo no painel direito, abaixo da lista e botões
        self.tempo_atual = 0
        self.scale_tempo = tk.Scale(self.frame_direito, from_=0, to=10, orient=tk.HORIZONTAL, label="Tempo", command=self.mudar_tempo)
        self.scale_tempo.pack(fill=tk.X, padx=10, pady=10)

        self.carregar_pontos()
        self.atualizar_lista()
        self.desenhar_pontos()

    def mudar_tempo(self, val):
        self.tempo_atual = int(val)
        self.atualizar_lista()
        self.desenhar_pontos()

    def desenhar_pontos(self):
        for art in self.pontos_artist:
            art.remove()
        self.pontos_artist.clear()

        for p in self.pontos:
            if isinstance(p, dict) and 't' in p and p['t'] == self.tempo_atual:
                art = self.ax.plot(p['x'], p['y'], 'bo')[0]
                text = self.ax.text(p['x'] + 0.02, p['y'] + 0.02, p['nome'], fontsize=9)
                self.pontos_artist.append(art)
                self.pontos_artist.append(text)

        self.canvas.draw()

    def solicitar_nome(self):
        return simpledialog.askstring("Nome do ponto", "Digite o nome da pessoa ou relação:")

    def encontrar_ponto_proximo(self, x, y, tolerancia=0.03):
        for p in self.pontos:
            if p['t'] == self.tempo_atual:
                if np.hypot(p['x'] - x, p['y'] - y) <= tolerancia:
                    return p
        return None

    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        x, y = event.xdata, event.ydata
        ponto = self.encontrar_ponto_proximo(x, y)

        if event.dblclick:
            if ponto:
                self.pontos.remove(ponto)
                self.desenhar_pontos()
                self.salvar_pontos()
                self.atualizar_lista()
            else:
                nome = self.solicitar_nome()
                if nome:
                    self.adicionar_ponto(x, y, nome, self.tempo_atual)
        else:
            if ponto:
                self.dragging_point = ponto

    def on_motion(self, event):
        if self.dragging_point and event.inaxes == self.ax and event.button == 1:
            p = self.dragging_point
            p['x'] = event.xdata
            p['y'] = event.ydata
            self.desenhar_pontos()

    def on_release(self, event):
        if self.dragging_point:
            self.salvar_pontos()
            self.atualizar_lista()
            self.dragging_point = None

    def adicionar_ponto(self, x, y, nome, t):
        self.pontos.append({'x': x, 'y': y, 'nome': nome, 't': t})
        self.desenhar_pontos()
        self.salvar_pontos()
        self.atualizar_lista()

    def adicionar_ponto_manual(self):
        nome = self.solicitar_nome()
        if not nome:
            return

        try:
            x = float(simpledialog.askstring("Coordenada X", "Digite a coordenada X (entre -1 e 1):"))
            y = float(simpledialog.askstring("Coordenada Y", "Digite a coordenada Y (entre -1 e 1):"))
        except (TypeError, ValueError):
            messagebox.showerror("Erro", "Coordenadas inválidas.")
            return

        if not (-1 <= x <= 1) or not (-1 <= y <= 1):
            messagebox.showerror("Erro", "As coordenadas devem estar entre -1 e 1.")
            return

        self.adicionar_ponto(x, y, nome, self.tempo_atual)

    def deletar_ponto_selecionado(self):
        selecao = self.lista.curselection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um ponto para remover.")
            return
        index = selecao[0]

        pontos_do_tempo = [p for p in self.pontos if isinstance(p, dict) and 't' in p and p['t'] == self.tempo_atual]

        ponto = pontos_do_tempo[index]
        self.pontos.remove(ponto)
        self.desenhar_pontos()
        self.salvar_pontos()
        self.atualizar_lista()

    def salvar_pontos(self):
        with open('pontos.json', 'w') as f:
            json.dump(self.pontos, f, indent=4)

    def carregar_pontos(self):
        if os.path.exists('pontos.json'):
            with open('pontos.json', 'r') as f:
                try:
                    self.pontos = json.load(f)
                except Exception as e:
                    # messagebox.showerror("Erro", f"Erro ao carregar pontos: {e}")
                    self.pontos = []


    def copiar_pontos_para_tempo_seguinte(self):
        tempo_destino = self.tempo_atual + 1
        
        # Copia pontos do tempo atual para o tempo seguinte
        pontos_atuais = [p for p in self.pontos if p.get('t') == self.tempo_atual]
        for p in pontos_atuais:
            novo_ponto = {'x': p['x'], 'y': p['y'], 'nome': p['nome'], 't': tempo_destino}
            self.pontos.append(novo_ponto)
        
        # Ajusta o slider caso ultrapasse o máximo
        if tempo_destino > self.scale_tempo['to']:
            self.scale_tempo.config(to=tempo_destino)
        
        # Atualiza o valor do slider para o novo tempo
        self.scale_tempo.set(tempo_destino)
        self.tempo_atual = tempo_destino
        
        self.salvar_pontos()
        self.atualizar_lista()
        self.desenhar_pontos()

        messagebox.showinfo("Copiar pontos", f"Pontos copiados do tempo {self.tempo_atual - 1} para o tempo {tempo_destino}.")

    def apagar_pontos_tempo_atual(self):
        confirm = messagebox.askyesno("Confirmação", f"Tem certeza que deseja apagar TODOS os pontos do tempo {self.tempo_atual}?")
        if confirm:
            self.pontos = [p for p in self.pontos if p.get('t') != self.tempo_atual]
            self.salvar_pontos()
            self.atualizar_lista()
            self.desenhar_pontos()

    def atualizar_lista(self):
        self.lista.delete(0, tk.END)
        pontos_do_tempo = [p for p in self.pontos if isinstance(p, dict) and 't' in p and p['t'] == self.tempo_atual]
        for p in pontos_do_tempo:
            self.lista.insert(tk.END, f"{p['nome']} ({p['x']:.2f}, {p['y']:.2f})")

    def fechar_programa(self):
        self.salvar_pontos()  # Garante que tudo esteja salvo
        plt.close(self.fig)   # Fecha a figura do matplotlib corretamente
        self.root.destroy()   # Fecha a janela principal



if __name__ == "__main__":
    root = tk.Tk()
    app = PlanoAfetivo(root)
    root.protocol("WM_DELETE_WINDOW", app.fechar_programa)
    root.mainloop()

