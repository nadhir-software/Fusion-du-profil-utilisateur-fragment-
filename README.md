# Maha These

Environnement Python de base pour data science et IA.

## Mise en place

1. Créer l'environnement virtuel:

```powershell
"C:/Users/Nadhir bh/AppData/Local/Programs/Python/Python311/python.exe" -m venv .venv
```

2. Activer l'environnement:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Installer les dépendances:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

Pour la pile IA complète, installez aussi:

```powershell
pip install -r requirements-ai.txt
```

4. Enregistrer le noyau Jupyter:

```powershell
python -m ipykernel install --user --name maha_these --display-name "Python (maha_these)"
```

5. Lancer Jupyter Lab:

```powershell
jupyter lab
```

## Arborescence

- `src/maha_these`: code du projet
- `notebooks/`: analyse exploratoire et prototypage
- `data/`: jeux de données locaux
- `models/`: artefacts entraînés
- `reports/figures/`: graphiques et exports
