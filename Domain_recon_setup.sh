#!/bin/bash

echo "[+] Updating system..."
sudo apt update -y

echo "[+] Installing Python + Tkinter..."
sudo apt install -y python3 python3-pip python3-tk

echo "[+] Installing required system utilities..."
sudo apt install -y grep gawk curl git

echo "[+] Installing Go..."
if ! command -v go &> /dev/null
then
    sudo apt install -y golang
fi

echo "[+] Setting up Go PATH..."
if ! grep -q 'export PATH=$PATH:$HOME/go/bin' ~/.bashrc; then
    echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
fi

export PATH=$PATH:$HOME/go/bin

echo "[+] Installing subfinder..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

echo "[+] Installing assetfinder..."
go install -v github.com/tomnomnom/assetfinder@latest

echo "[+] Installing httpx..."
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

echo ""
echo "========================================"
echo "✅ Installation Completed Successfully!"
echo "========================================"
echo ""
echo "Verify installation:"
echo "  python3 --version"
echo "  subfinder -h"
echo "  assetfinder -h"
echo "  httpx -h"
echo ""
echo "Restart your terminal or run:"
echo "  source ~/.bashrc"
echo ""
