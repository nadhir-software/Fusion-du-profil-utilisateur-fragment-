# RUNBOOK — Lancer le pipeline fédéré réel

Procédure complète pour exécuter le pipeline **crawl → preprocess → fragment →
train (LoRA) → agrégation (FedAvg) → génération de profil**, et peupler le
dashboard avec de vrais profils.

> Rappel confidentialité : les données brutes ne touchent jamais le disque
> (RAM only via `SessionBuffer`). Seuls les Δθ (poids LoRA) et le profil final
> anonymisé quittent la session.

---

## 1. Prérequis matériels

| Ressource | Recommandé | Raison |
|---|---|---|
| GPU | NVIDIA ≥ 8 Go VRAM (12 Go confortable) | QLoRA 4-bit sur Mistral-7B |
| RAM | ≥ 16 Go | chargement modèle + tokenisation |
| Disque | ~20 Go libres | poids Mistral-7B (~15 Go) + caches |

Sur CPU seul, l'entraînement est **très** lent (heures) — un GPU CUDA est
fortement conseillé. `bitsandbytes` (4-bit) requiert CUDA sous Linux/WSL ; sous
Windows natif, préférez WSL2 ou désactivez `load_in_4bit` (config `training`).

---

## 2. Installer les dépendances

```powershell
# Depuis la racine du dépôt, environnement virtuel activé
pip install -e ".[ai]"      # torch, transformers, peft, trl, sentence-transformers…
pip install -e ".[crawl]"   # praw, playwright, beautifulsoup4

# Navigateur headless pour LinkedIn/Amazon
python -m playwright install chromium

# bitsandbytes (QLoRA) — sous Linux/WSL uniquement
pip install bitsandbytes
```

---

## 3. Identifiants & accès

### 3.1 Reddit (crawler)
1. Aller sur https://www.reddit.com/prefs/apps → **create app** → type **script**.
2. Noter le `client_id` (sous le nom de l'app) et le `client_secret`.

### 3.2 HuggingFace + Mistral-7B
1. Créer un token : https://huggingface.co/settings/tokens
2. Accepter la licence du modèle :
   https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3
3. `huggingface-cli login` (ou variable `HUGGINGFACE_TOKEN`).

### 3.3 Fichier `.env`
Copier `.env.example` → `.env` et renseigner :

```dotenv
REDDIT_CLIENT_ID=xxxxxxxx
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxxxx
REDDIT_USER_AGENT=FederatedProfiler/1.0
HUGGINGFACE_TOKEN=hf_xxxxx
```

---

## 4. Lancer le pipeline

### Option A — CLI (exécution autonome, affiche le profil)

```powershell
python scripts/run_pipeline.py --reddit spez `
  --linkedin "https://www.linkedin.com/in/xxxx/" `
  --amazon   "https://www.amazon.com/gp/profile/xxxx/"
```

Affiche le résumé JSON + le `user_hash` unifié. ⚠️ Le profil est généré dans le
process du script (RAM) : cette commande **ne peuple pas** le dashboard.

### Option B — Via l'API (peuple le dashboard)

Le pipeline doit tourner **dans le process de l'API** pour que le profil
atterrisse dans le registre RAM lu par le dashboard.

```powershell
# 1. Lancer l'API (charge le .env)
uvicorn maha_these.layer5_api.main:app --reload   # http://localhost:8000

# 2. Déclencher le pipeline (tâche de fond dans le process API)
curl -X POST http://localhost:8000/api/v1/crawl `
  -H "Content-Type: application/json" `
  -d '{"reddit_username":"spez","linkedin_url":"https://www.linkedin.com/in/xxx/","amazon_profile_url":""}'
# -> {"status":"started","job_id":"...","user_hash":"<HASH>"}

# 3. Une fois l'entraînement terminé (voir logs uvicorn), récupérer le profil
curl http://localhost:8000/api/v1/profile/<HASH>
```

Dans le dashboard (http://localhost:5173), onglet **Profil**, saisir `<HASH>`.

> Le `user_hash` est renvoyé immédiatement par `POST /crawl` ; le profil, lui,
> n'est disponible qu'à la fin de l'entraînement (plusieurs minutes selon GPU).

---

## 5. Paramétrage

Tous les hyperparamètres sont dans `config/config.yaml` :
- `lora` (r, alpha, dropout, cibles), `training` (epochs, lr, `load_in_4bit`…)
- `federated` (`algorithm`: fedavg | fedprox | secure ; `mu` ; `dp_noise_sigma`)

---

## 6. Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `ImportError: praw / playwright / peft` | extra non installé | `pip install -e ".[ai]"` / `".[crawl]"` |
| `OSError: ... Mistral-7B ... gated` | licence HF non acceptée | accepter la licence + `huggingface-cli login` |
| `bitsandbytes` échoue (Windows) | CUDA/4-bit non supporté | utiliser WSL2, ou `load_in_4bit: false` |
| Profil vide / `json_parse_failed` | sortie LLM non-JSON | augmenter `max_new_tokens`, ajuster le prompt |
| `GET /profile/<hash>` → 404 | pipeline pas terminé / process séparé | attendre la fin ; utiliser l'Option B (API) |

---

## 7. Recommandation seule (sans entraînement)

Pour activer uniquement les onglets **Recommandation** / **Ciblage** (moteur
content-based), `sentence-transformers` suffit — pas besoin de Mistral ni
d'entraînement :

```powershell
pip install sentence-transformers
```

Le premier appel télécharge le modèle `all-mpnet-base-v2` (~400 Mo).

---

## 8. Store de profils partagé (multi-process / multi-workers)

Par défaut, les profils vivent dans un registre RAM **local au process**
(`PROFILE_STORE_BACKEND=memory`). Le CLI et l'API ne le partagent donc pas, et
lancer l'API avec plusieurs workers casserait la cohérence.

Pour partager les profils entre le CLI, l'API et **N** workers — tout en
respectant le « no disk » — utiliser **Redis en mode RAM-only** (persistance
désactivée : ni RDB, ni AOF) :

```bash
# Lancer Redis SANS persistance (rien n'est écrit sur disque)
redis-server --save "" --appendonly no
# ...ou via Docker :
docker run --rm -p 6379:6379 redis:7 redis-server --save "" --appendonly no
```

Installer le client et activer le backend :

```powershell
pip install -e ".[redis]"
```

Dans `.env` :

```dotenv
PROFILE_STORE_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
```

L'interface est identique (`ProfileStore.save/load/load_all/clear`) : aucun
autre changement de code. On peut alors lancer plusieurs workers :

```powershell
uvicorn maha_these.layer5_api.main:app --workers 4
```

> Vérifier que Redis est bien sans persistance : `redis-cli config get save`
> doit renvoyer une valeur vide, et `appendonly` doit être `no`. Ainsi aucune
> donnée n'atterrit sur disque.
