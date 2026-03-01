#!/bin/bash

VENV_DIR="venv"

MAIN_FILE="main.py"

create_venv() {
    echo "Criando ambiente virtual..."
    python3 -m venv $VENV_DIR

    echo "Ativando ambiente virtual..."
    source $VENV_DIR/bin/activate

    echo "Instalando dependências..."
    pip install --upgrade pip
    pip install -r requirements.txt 2>/dev/null || pip install ccxt pandas numpy scikit-learn

    echo "Ambiente virtual pronto!"
}

run_project() {
    echo "Rodando projeto..."
    source $VENV_DIR/bin/activate
    python $MAIN_FILE
}

if [ ! -d "$VENV_DIR" ]; then
    create_venv
else
    echo "Ambiente virtual já existe, apenas rodando o projeto..."
fi

run_project