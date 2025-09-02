#!/usr/bin/env python3
"""
GOHLCC Advanced Anonymization Tool
"""

import os
import sys
import time
import subprocess
import requests
import socket
import threading
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.live import Live
import pyfiglet

class GOHLCCAnonymizer:
    def __init__(self):
        self.console = Console()
        self.interface = "eth0"  # Modifiable
        self.is_running = False
        self.current_ip = None
        self.original_ip = None
        self.session_start = None
        self.ip_changes = 0
        self.mac_changes = 0
        
    def clear_screen(self):
        """Nettoie l'écran avec style"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def display_banner(self):
        """Affiche le banner stylé"""
        self.clear_screen()
        
        # ASCII Art avec style
        title = pyfiglet.figlet_format("GOHLCC", font="slant")
        subtitle = "Advanced Anonymization Tool"
        
        banner_text = Text(title, style="bold cyan")
        subtitle_text = Text(subtitle, style="bold magenta")
        
        panel = Panel(
            Align.center(banner_text + "\n" + subtitle_text),
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
        
    def get_public_ip(self, via_tor=False):
        """Récupère l'IP publique avec ou sans Tor"""
        try:
            if via_tor:
                # Utilise proxychains pour passer par Tor
                result = subprocess.run(
                    ["proxychains", "curl", "-s", "--connect-timeout", "10", "https://ifconfig.me"],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            else:
                response = requests.get("https://ifconfig.me", timeout=10)
                return response.text.strip()
        except Exception as e:
            return f"Erreur: {str(e)}"
        return "Impossible de récupérer l'IP"
        
    def get_location_info(self, ip):
        """Récupère les informations de géolocalisation"""
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            data = response.json()
            if data['status'] == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', 'Unknown')
                }
        except:
            pass
        return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}
        
    def change_mac_address(self):
        """Change l'adresse MAC avec animation"""
        with self.console.status("[bold green]Changement d'adresse MAC...", spinner="dots"):
            try:
                # Désactive l'interface
                subprocess.run(["sudo", "ifconfig", self.interface, "down"], 
                             check=True, capture_output=True)
                time.sleep(1)
                
                # Change la MAC
                subprocess.run(["sudo", "macchanger", "-r", self.interface], 
                             check=True, capture_output=True)
                time.sleep(1)
                
                # Réactive l'interface
                subprocess.run(["sudo", "ifconfig", self.interface, "up"], 
                             check=True, capture_output=True)
                time.sleep(2)
                
                self.mac_changes += 1
                self.console.print("[bold green]Adresse MAC changée avec succès!")
                return True
                
            except subprocess.CalledProcessError as e:
                self.console.print(f"[bold red]Erreur lors du changement MAC: {e}")
                return False
                
    def start_tor_service(self):
        """Démarre le service Tor avec animation"""
        with self.console.status("[bold cyan]🚀 Démarrage du service Tor...", spinner="bouncingBall"):
            try:
                subprocess.run(["sudo", "service", "tor", "start"], 
                             check=True, capture_output=True)
                time.sleep(5)
                self.console.print("[bold green]Service Tor démarré!")
                return True
            except subprocess.CalledProcessError:
                self.console.print("[bold red]Erreur lors du démarrage de Tor")
                return False
                
    def setup_tor_routing(self):
        """Configure le routage Tor avec animation"""
        with self.console.status("[bold yellow]Configuration du routage Tor...", spinner="arc"):
            try:
                # Nettoie les règles iptables existantes
                subprocess.run(["sudo", "iptables", "-F"], check=True, capture_output=True)
                subprocess.run(["sudo", "iptables", "-t", "nat", "-F"], check=True, capture_output=True)
                
                # Configure les règles de redirection
                commands = [
                    ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "!", "--uid-owner", "debian-tor", "-p", "tcp", "--syn", "-j", "REDIRECT", "--to-ports", "9040"],
                    ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "5353"],
                    ["sudo", "iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
                    ["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "ACCEPT"],
                    ["sudo", "iptables", "-A", "OUTPUT", "-j", "REJECT"]
                ]
                
                for cmd in commands:
                    subprocess.run(cmd, check=True, capture_output=True)
                    time.sleep(0.5)
                    
                self.console.print("[bold green]Routage Tor configuré! Tout le trafic passe par Tor.")
                return True
                
            except subprocess.CalledProcessError as e:
                self.console.print(f"bold red]Erreur configuration routage: {e}")
                return False
                
    def new_tor_identity(self):
        """Génère une nouvelle identité Tor"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', 9051))
                s.send(b'AUTHENTICATE ""\nSIGNAL NEWNYM\nQUIT\n')
                time.sleep(3)
                self.ip_changes += 1
                return True
        except Exception:
            return False
            
    def display_status_dashboard(self):
        """Affiche un dashboard en temps réel"""
        layout = Layout()
        
        # Section du haut - Statut
        status_table = Table(title="Statut de l'Anonymisation", style="cyan")
        status_table.add_column("Paramètre", style="bold white")
        status_table.add_column("Valeur", style="green")
        
        current_time = datetime.now().strftime("%H:%M:%S")
        uptime = str(datetime.now() - self.session_start).split('.')[0] if self.session_start else "00:00:00"
        
        status_table.add_row("Heure", current_time)
        status_table.add_row("Uptime", uptime)
        status_table.add_row("Changements IP", str(self.ip_changes))
        status_table.add_row("Changements MAC", str(self.mac_changes))
        status_table.add_row("Interface", self.interface)
        
        # Section du bas - IPs
        ip_table = Table(title="Informations IP", style="magenta")
        ip_table.add_column("Type", style="bold white")
        ip_table.add_column("Adresse IP", style="yellow")
        ip_table.add_column("Pays", style="blue")
        ip_table.add_column("Ville", style="green")
        ip_table.add_column("FAI", style="cyan")
        
        if self.original_ip:
            orig_info = self.get_location_info(self.original_ip)
            ip_table.add_row("Originale", self.original_ip, orig_info['country'], orig_info['city'], orig_info['isp'])
            
        if self.current_ip:
            curr_info = self.get_location_info(self.current_ip)
            ip_table.add_row("Actuelle (Tor)", self.current_ip, curr_info['country'], curr_info['city'], curr_info['isp'])
        
        layout.split_column(
            Layout(status_table, size=10),
            Layout(ip_table)
        )
        
        return Panel(layout, border_style="bright_blue", padding=(1, 2))
        
    def interactive_menu(self):
        """Menu interactif principal"""
        while True:
            self.display_banner()
            
            menu = Table(title="Menu Principal", style="bold cyan")
            menu.add_column("Option", style="bold white")
            menu.add_column("Description", style="green")
            
            menu.add_row("1", "Vérifier IP actuelle")
            menu.add_row("2", "Changer adresse MAC")
            menu.add_row("3", "Démarrer Tor")
            menu.add_row("4", "Configurer routage Tor")
            menu.add_row("5", "Nouvelle identité Tor")
            menu.add_row("6", "Mode automatique")
            menu.add_row("7", "Dashboard temps réel")
            menu.add_row("8", "Paramètres")
            menu.add_row("9", "Quitter")
            
            self.console.print(menu)
            self.console.print()
            
            choice = Prompt.ask("[bold cyan]Choisissez une option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"])
            
            if choice == "1":
                self.check_current_ip()
            elif choice == "2":
                self.change_mac_address()
            elif choice == "3":
                self.start_tor_service()
            elif choice == "4":
                self.setup_tor_routing()
            elif choice == "5":
                self.request_new_identity()
            elif choice == "6":
                self.auto_mode()
            elif choice == "7":
                self.real_time_dashboard()
            elif choice == "8":
                self.settings_menu()
            elif choice == "9":
                self.console.print("[bold yellow]Merci d'avoir utilisé GOHLCC Anonymizer!")
                break
                
            if choice != "6" and choice != "7":
                input("\n⏎ Appuyez sur Entrée pour continuer...")
                
    def check_current_ip(self):
        """Vérifie l'IP actuelle"""
        self.console.print(Panel("[bold cyan]Vérification des adresses IP...", border_style="cyan"))
        
        # IP sans Tor
        with self.console.status("[bold blue]Récupération IP publique...", spinner="dots"):
            original_ip = self.get_public_ip(via_tor=False)
            if not self.original_ip:
                self.original_ip = original_ip
                
        # IP avec Tor
        with self.console.status("[bold green]Récupération IP via Tor...", spinner="dots"):
            tor_ip = self.get_public_ip(via_tor=True)
            self.current_ip = tor_ip
            
        # Affichage des résultats
        result_table = Table(title="Résultats IP", style="bold")
        result_table.add_column("Type", style="bold white")
        result_table.add_column("Adresse IP", style="yellow")
        result_table.add_column("Statut", style="green")
        
        result_table.add_row("Sans Tor", original_ip, "Directe")
        result_table.add_row("Avec Tor", tor_ip, "Anonyme" if tor_ip != original_ip else "⚠️ Problème")
        
        self.console.print(result_table)
        
    def request_new_identity(self):
        """Demande une nouvelle identité"""
        with self.console.status("[bold magenta]Génération nouvelle identité...", spinner="aesthetic"):
            success = self.new_tor_identity()
            if success:
                time.sleep(3)
                new_ip = self.get_public_ip(via_tor=True)
                self.current_ip = new_ip
                self.console.print(f"[bold green]Nouvelle identité générée! IP: {new_ip}")
            else:
                self.console.print("[bold red]Erreur lors de la génération d'identité")
                
    def auto_mode(self):
        """Mode automatique avec boucle de changements"""
        self.console.print(Panel("[bold green]Mode Automatique Activé", border_style="green"))
        self.console.print("[yellow]Changements automatiques toutes les 20 secondes")
        self.console.print("[red]Ctrl+C pour arrêter\n")
        
        self.session_start = datetime.now()
        
        try:
            while True:
                # Change MAC
                self.change_mac_address()
                time.sleep(2)
                
                # Nouvelle identité Tor
                with self.console.status("[bold cyan]Nouvelle identité...", spinner="point"):
                    self.new_tor_identity()
                    
                time.sleep(3)
                
                # Vérifie nouvelle IP
                with self.console.status("[bold yellow]🔍 Vérification IP...", spinner="bouncingBar"):
                    new_ip = self.get_public_ip(via_tor=True)
                    self.current_ip = new_ip
                    
                self.console.print(f"[bold green]Nouvelle IP: {new_ip}")
                self.console.print(f"[cyan]Changements: IP({self.ip_changes}) | MAC({self.mac_changes})")
                self.console.print("[yellow]Attente 20 secondes...\n")
                
                time.sleep(20)
                
        except KeyboardInterrupt:
            self.console.print("\n🛑 [bold red]Mode automatique arrêté")
            
    def real_time_dashboard(self):
        """Dashboard en temps réel"""
        self.session_start = datetime.now() if not self.session_start else self.session_start
        
        try:
            with Live(self.display_status_dashboard(), refresh_per_second=1, screen=True) as live:
                while True:
                    time.sleep(1)
                    live.update(self.display_status_dashboard())
        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Dashboard fermé")
            
    def settings_menu(self):
        """Menu des paramètres"""
        self.console.print(Panel("[bold cyan]Paramètres", border_style="cyan"))
        
        new_interface = Prompt.ask(f"Interface réseau actuelle: {self.interface}. Nouvelle interface", default=self.interface)
        self.interface = new_interface
        
        self.console.print(f"[bold green]Interface mise à jour: {self.interface}")
        
    def initial_setup(self):
        """Configuration initiale"""
        self.display_banner()
        
        self.console.print(Panel("🚀 [bold cyan]Configuration Initiale GOHLCC", border_style="bright_blue"))
        
        # Vérification des permissions
        if os.geteuid() != 0:
            self.console.print("[bold yellow]Attention: Certaines fonctions nécessitent les privilèges root")
            if not Confirm.ask("Continuer sans privilèges root?"):
                sys.exit(1)
                
        # Configuration interface
        self.interface = Prompt.ask("Interface réseau", default="eth0")
        
        self.console.print("[bold green]Configuration terminée!")
        time.sleep(2)
        
    def run(self):
        """Lance l'application"""
        try:
            self.initial_setup()
            self.interactive_menu()
        except KeyboardInterrupt:
            self.console.print("\nbold yellow]Au revoir!")
        except Exception as e:
            self.console.print(f"\n[bold red]Erreur critique: {e}")

def main():
    """Point d'entrée principal"""
    try:
        # Vérification des dépendances
        required_packages = ["requests", "rich", "pyfiglet"]
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
                
        if missing_packages:
            print(f"Packages manquants: {', '.join(missing_packages)}")
            print(f"Installez avec: pip install {' '.join(missing_packages)}")
            sys.exit(1)
            
        # Lance l'outil
        anonymizer = GOHLCCAnonymizer()
        anonymizer.run()
        
    except Exception as e:
        print(f"❌  Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
