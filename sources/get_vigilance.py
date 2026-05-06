import os
import time
import logging
import threading
import pandas as pd
from meteole import Vigilance
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meteole")

# Load local .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

APP_ID = os.environ.get("VIGILANCE_APP_ID")

vigi = Vigilance(application_id=APP_ID)
df_phenomenon, df_timelaps = vigi.get_phenomenon()

vigi_code = '8'
data = []

def select_domain_info(vigi_color_code: int):
    for domain, element in zip(df_timelaps["domain_id"], df_timelaps["phenomenon_items"]):
        for phenomenom in element:
            if phenomenom['phenomenon_id'] == str(vigi_color_code):
                data.append({'domain': domain, 'effect': phenomenom})

def thread_loop_update(vigi_color_code: int):
    timestamp = time.time()
    while(1):
        if ((time.time() - 172800) >= timestamp): # update data every 48h
            print("updating data")
            select_domain_info(vigi_color_code)
            timestamp = time.time()

def get_domain_colors(domain_code: str):
    color_by_days = []
    for item in data:
        if item['domain'] == domain_code:
            color_by_days.append(item['effect']['phenomenon_max_color_id'])
    return color_by_days

select_domain_info(vigi_code) # Récupère toutes les informations pour chaque département et pour une vigilance

# t = threading.Thread(target=thread_loop_update, args=(vigi_code))

# t.start()
# t.join()

df_departement = []
df_color = []
df_color_2 = []
for item in data:
    res = get_domain_colors(item['domain']) # Retourne les vigilances sur les deux jours pour un département ciblé
    if item['domain'] in df_departement:
        continue
    df_departement.append(item['domain'])
    df_color.append(res[0])
    df_color_2.append(res[1])
df = pd.DataFrame()
df = df.assign(departement = df_departement)
df = df.assign(color = df_color)
df = df.assign(color_2 = df_color_2)
print(df)
