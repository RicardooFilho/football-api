import os
import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE = "America/Sao_Paulo"

LIGAS = {
    71:  "Brasileirão Série A",
    13:  "Libertadores",
    11:  "Sul-Americana",
    73:  "Copa do Brasil",
    475: "Paulistão",
    39:  "Premier League",
    140: "La Liga",
    78:  "Bundesliga",
    61:  "Ligue 1",
    135: "Serie A (Itália)",
    2:   "Champions League",
}

API_FOOTBALL_URL = "https://v3.football.api-sports.io/fixtures"

def buscar_jogos_do_dia(api_key: str) -> list[dict]:

    hoje = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d")

    headers = {"x-apisports-key": api_key}
    params = {"date": hoje, "timezone": TIMEZONE}

    resp = requests.get(API_FOOTBALL_URL, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    dados = resp.json()

    if dados.get("errors"):
        raise RuntimeError(f"API retornou erro: {dados['errors']}")

    todos_os_jogos = dados.get("response", [])

    jogos_filtrados = [
        jogo for jogo in todos_os_jogos
        if jogo["league"]["id"] in LIGAS
    ]

    return jogos_filtrados


def formatar_mensagem(jogos: list[dict]) -> str:

    hoje_formatado = datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y")

    if not jogos:
        return f"Nenhum jogo das ligas acompanhadas hoje."

    jogos_por_liga: dict[int, list[dict]] = {}
    for jogo in jogos:
        liga_id = jogo["league"]["id"]
        jogos_por_liga.setdefault(liga_id, []).append(jogo)

    linhas = [f"⚽ *Jogos de hoje ({hoje_formatado})*", ""]

    for liga_id, nome_liga in LIGAS.items():
        if liga_id not in jogos_por_liga:
            continue

        linhas.append(f"🏆 *{nome_liga}*")

        jogos_da_liga = sorted(
            jogos_por_liga[liga_id],
            key=lambda j: j["fixture"]["timestamp"]
        )

        for jogo in jogos_da_liga:
            horario = datetime.fromtimestamp(
                jogo["fixture"]["timestamp"], tz=ZoneInfo(TIMEZONE)
            ).strftime("%H:%M")
            time_casa = jogo["teams"]["home"]["name"]
            time_fora = jogo["teams"]["away"]["name"]
            linhas.append(f"{horario} - {time_casa} x {time_fora}")

        linhas.append("")

    return "\n".join(linhas).strip()


def enviar_whatsapp(mensagem: str, phone: str, apikey: str) -> None:

    url = "https://api.callmebot.com/whatsapp.php"
    params = {"phone": phone, "text": mensagem, "apikey": apikey}

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()

    if resp.status_code == 200:
        print("Mensagem enviada com sucesso para o WhatsApp.")
    else:
        print(f"CallMeBot retornou status inesperado: {resp.status_code}")

def main():
    api_key = os.environ.get("API_FOOTBALL_KEY")
    phone = os.environ.get("CALLMEBOT_PHONE")
    callmebot_key = os.environ.get("CALLMEBOT_APIKEY")

    faltando = [
        nome for nome, valor in [
            ("API_FOOTBALL_KEY", api_key),
            ("CALLMEBOT_PHONE", phone),
            ("CALLMEBOT_APIKEY", callmebot_key),
        ] if not valor
    ]
    if faltando:
        print(f"ERRO: variáveis de ambiente faltando: {', '.join(faltando)}")
        sys.exit(1)

    print("Buscando jogos do dia...")
    jogos = buscar_jogos_do_dia(api_key)
    print(f"{len(jogos)} jogo(s) encontrado(s) nas ligas acompanhadas.")

    mensagem = formatar_mensagem(jogos)
    print("--- Mensagem que será enviada ---")
    print(mensagem)
    print("----------------------------------")

    enviar_whatsapp(mensagem, phone, callmebot_key)


if __name__ == "__main__":
    main()
