import time

# import os
from dotenv import load_dotenv
from google import genai

# from pydantic import BaseModel
queue = {}
def main(fid: int, data: dict):
    load_dotenv()
    # print("GEMINI_API_KEY" in os.environ)
    client = genai.Client()

    # 質の高い統計分析に必要なデータを洗い出す
    # print(data["meta"]["winner"]) # 勝者
    # print(data["meta"]["total_ticks"]) # 試合時間（0〜300ティック）
    # print(data["meta"]["core_damage_by_team"]["TEAM_A"]) # チームAが与えたダメージ量
    # print(data["meta"]["core_damage_by_team"]["TEAM_B"]) # チームBが与えたダメージ量
    # print(data["meta"]["final_core_hp"]) # 試合終了時点での各プレイヤーの残りHP dict_keys(['A1', 'A2', 'A3', 'B1', 'B2', 'B3'])
    # print(data["meta"]["player_factions"]) # 各プレイヤーの使用勢力（None の場合あり）
    # print(data["meta"]["player_names"]) # 誰がプレイしているか（None の場合あり）
    # print(data["meta"]["allied_lord"]) # 試合中のロードの状態 ('owner', 'hp', 'target', 'path', 'ready_tick', 'arrival_tick', 'support_units', 'alive', 'expended')
    # print(data["meta"]["winner_type"]) # 勝利の種類
    # 重要なティックと、そこで発生するイベント（例：コアの撃破）を特定する
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
    #                     print(ticknumber) # すべてを辞書で管理する案：戦闘開始 → 戦闘終了
    #                     found = True
    #             except KeyError:
    #                 pass
    coreDestroyedTicks = []
    for tick in data["ticks"]:
        for event in tick["events"]:
            try:
                if event["type"] == "BATTLE_RESOLVED" and event["location_id"] in lid and event["core_destroyed"] is True:
                    # print(tick["tick"]) # ティック番号
                    coreDestroyedTicks.append(tick)
                    # foundbattlestart(tick["tick"], event["location_id"])
            except KeyError:
                pass
    # print(coreDestroyedTicks[0].keys())

    # コアの破壊（クラッシュ）を列挙する
    geminiinputcrash = ""
    for oneTick in coreDestroyedTicks:
        for coreDT in oneTick["events"]:
            try:
                geminiinputcrash += f"""<crash> {oneTick["tick"]}ティック目に、プレイヤー{coreDT["core_owner"]}のコアが、攻撃側のプレイヤー{coreDT["winner"]}によって破壊された </crash>, \n"""
            except KeyError:
                pass
    # print(geminiinput)

    # ロードの状態を判定する
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
                break
        except KeyError:
            pass

    # Gemini へのリクエストを組み立てる
    if owner == "":
        geminiinputlord = "<lord>ロードは召喚されなかった</lord>"
    else:
        geminiinputlord = f"<lord>ロードは{capturelordtick}ティック目にプレイヤー{owner}によって撃破され、{teamowner}の味方として召喚された</lord>"
    # print(geminiinputlord)

    try:
        player_names = data["meta"]["player_names"]
    except KeyError:
        player_names = "名前がありません"

    try:
        start = time.perf_counter()
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            system_instruction="""あなたは、プレイヤーが3対3で戦うバーチャルeスポーツRTSゲームの試合アナリストです。
            あなたの役割は、試合を分析し、ゲームで何が起きたのかを解説することです。
            ゲームはティック単位で進行します。
            <data> は、この試合について入手できるすべてのデータです。
            <winner> は試合の勝者、<time> は試合時間、<names> はプレイヤー名、<fractions> はプレイヤーの勢力、
            <lord> はロードに関する情報（ロードとは、マップ中央にいる強力な中立ユニットです。いずれかのチームに倒されると、そのチームの味方となって敵のコアへプッシュします）、
            <crash> はコアが破壊されたティックに関する情報です。
            プレイヤーには A1、A2、A3、B1、B2、B3 というキーが割り当てられています。
            プレイヤー名のデータが提供されている場合は、キーの代わりにその名前を使ってください（提供されていない場合は、無名の新人プレイヤーだとみなしてください）。
            A のプレイヤーが一方のチーム、B のプレイヤーがもう一方のチームです。
            回答はすべて自然な日本語で行ってください。""",
            input=f"""<data>
            <winner>{data["meta"]["winner"]}</winner>
            <time>{data["meta"]["total_ticks"]}</time>
            <names>{player_names}</names>
            <fractions>{data["meta"]["player_factions"]}</fractions>
            {geminiinputlord}
            {geminiinputcrash}
            </data>"""
        )
        elapsed = time.perf_counter() - start
        print(f"{elapsed:.3f} 秒")
        print(interaction.output_text)
        print(interaction.usage)
        queue[fid]["result"]["text"] = interaction.output_text
        queue[fid]["result"]["status"] = "完了"
    except Exception:  # noqa: BLE001
        queue[fid]["result"]["text"] = "error"
        queue[fid]["result"]["status"] = "error"