import json
import time

# import os
from dotenv import load_dotenv
from google import genai

# from pydantic import BaseModel

load_dotenv()
# print("GEMINI_API_KEY" in os.environ)
client = genai.Client()

with open("replays/01_league_league_16147200961505151604.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# определить какие данные нужны для качественного анализа статистики
# print(data["meta"]["winner"]) # победитель
# print(data["meta"]["total_ticks"]) # длительность матча от 0 до 300 тиков
# print(data["meta"]["core_damage_by_team"]["TEAM_A"]) # сколько нанесла урона команда А
# print(data["meta"]["core_damage_by_team"]["TEAM_B"]) # сколько нанесла урона команда B
# print(data["meta"]["final_core_hp"]) # сколько осталось хп на конец матча у каждого игрока dict_keys(['A1', 'A2', 'A3', 'B1', 'B2', 'B3'])
# print(data["meta"]["player_factions"]) # на ком играют? может быть none
# print(data["meta"]["player_names"]) # кто играет? может быть none
# print(data["meta"]["allied_lord"]) # состояние лорда в матче ('owner', 'hp', 'target', 'path', 'ready_tick', 'arrival_tick', 'support_units', 'alive', 'expended')
# print(data["meta"]["winner_type"]) # тип победы 
# определить ключевые тики и события которые на них происходят, например убийство ядра 
# location_id winner participants core_owner
lid = {"A1", "A2", "A3", "B1", "B2", "B3"}
# def foundbattlestart(ticknumber, resolvedevent):
#     found = False
#     print(ticknumber)
#     while (found is False) and (ticknumber > 0):
#         ticknumber -= 1
#         for event in data["ticks"][ticknumber]["events"]:
#             try:
#                 if event["type"] == "BATTLE_STARTED" and event["location_id"] == resolvedevent:
#                     print(ticknumber) # предлагаю хранить все в словаре: начало битвы - конец битвы
#                     found = True
#             except KeyError:
#                 pass
coreDestroyedTicks = []
for tick in data["ticks"]:
    for event in tick["events"]:
        try:
            if event["type"] == "BATTLE_RESOLVED" and event["location_id"] in lid and event["core_destroyed"] is True:
                # print(tick["tick"]) # номер тика
                coreDestroyedTicks.append(tick)
                # foundbattlestart(tick["tick"], event["location_id"])
        except KeyError:
            pass
# print(coreDestroyedTicks[0].keys())

# перечисляем краши ядер
geminiinputcrash = ""
for oneTick in coreDestroyedTicks:
    for coreDT in oneTick["events"]:
        try:
            geminiinputcrash += f"""<crash> на тике {oneTick["tick"]} ядро игрока {coreDT["core_owner"]} было уничтожено, нападавшим игроком {coreDT["winner"]} </crash>, \n"""
        except KeyError:
            pass
# print(geminiinput)

# определяем состояние лорда
geminiinputlord = ""
pid = {"A1", "A2", "A3", "B1", "B2", "B3"} #player_id
capturelordtick = 0
owner = ""
teamowner = ""
for tick in data["ticks"]:
    try:
        if tick["baron"]["allied_lord_owner"] in pid:
            capturelordtick = tick["tick"]
            owner = tick["baron"]["allied_lord_owner"]
            if owner[0] == "A":
                teamowner = "TEAM_A"
            else:
                teamowner = "TEAM_B"
    except KeyError:
        pass

# формируем запрос для гемини
if owner == "":
    geminiinputlord = "<lord>лорд не был призван</lord>"
else:
    geminiinputlord = f"<lord>лорд был повержен на {capturelordtick} тике, игроком {owner}, и был призван за команду {teamowner}</lord>"
# print(geminiinputlord)

# start = time.perf_counter()
# interaction = client.interactions.create(
#     model="gemini-3.6-flash",
#     system_instruction="""ты - аналитик матча по виртуальной киберспортивной rts игре, 
#     в которой сражаются игроки 3 на 3. твоя задача - проанализировать матч и рассказать, что произошло в игре.
#     игра двигается по тикам. 
#     <data> - это все доступные данные по матчу. <winner> - победитель матча, <time> - длительность матча, <names> - имена игроков,
#     <fractions> - фракции игроков, <lord> - информация о лорде (сильный нейтральный юнит в центре карты, который при
#     уничтожение одной из команд встает на ее сторону и пушит ядро), <crash> - информация о тике, в котором было
#     сломано ядро. у игроков есть ключи A1 A2 A3 B1 B2 B3, используй вместо этих ключей имена, если таковые данные
#     тебе были предоставлены (если нет, то считай их безымянными новичками), игроки A - одна команда, игроки B - другая команда""",
#     input=f"""<data>
#     <winner>{data["meta"]["winner"]}</winner>
#     <time>{data["meta"]["total_ticks"]}</time>
#     <names>{data["meta"]["player_names"]}</names>
#     <fractions>{data["meta"]["player_factions"]}</fractions>
#     {geminiinputlord}
#     {geminiinputcrash}
#     </data>"""
# )
# elapsed = time.perf_counter() - start

# print(f"{elapsed:.3f} с")      
# print(interaction.output_text)
# print(interaction.usage)