#! /usr/bin/python3
# Print games for a club in a season in JSON format

import argparse
import hashlib
import json
import re
from datetime import datetime
from enum import Enum

import requests
from bs4 import BeautifulSoup


class Scope(Enum):
    ALL = "all"
    SCHEDULE_ONLY = "schedule_only"
    SCORE_ONLY = "score_only"


class GameRecord(object):
    """docstring for GameRecord"""

    def __init__(self, uid, date, place, team_home, team_away, score_home, score_away, is_home):
        self.uid = uid
        self.date = date
        self.place = place
        self.team_home = team_home
        self.team_away = team_away
        self.score_home = score_home
        self.score_away = score_away
        self.is_home = is_home


def hash_of_game(club_id, tour, roundz):
    h = hashlib.sha1()
    rec = f'{club_id}_{tour}_{roundz}'
    h.update(rec.encode())
    return h.hexdigest()


def find_content_id(soup, season_n):
    panel_headings = soup.find_all(class_='panel-heading')
    res = []
    for el in panel_headings:
        for sub_header in el.find_all(class_='game-result__subheader'):
            if f'{season_n}-й' in sub_header.text:
                res.append(int(el.get('id').replace("heading", "")))
    return res


def find_scores(soup, content_id, club_id):
    games_panel = soup.find(id=f'collapse{content_id}')
    table_resp = games_panel.find_all(class_='table-responsive')[0]
    table = table_resp.find('table', attrs={'class': 'team-roster-table'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    a_cells = table_body.find_all('td')
    cell_count = 9
    if len(a_cells) % cell_count != 0:
        return []
    rec_count = int(len(a_cells) / cell_count)
    g_recs = []
    for x in range(rec_count):
        tour = a_cells[x * cell_count + 0].find(string=True)
        roundz = a_cells[x * cell_count + 1].find(string=True)
        date = a_cells[x * cell_count + 2].find(string=True)
        day_of_week = a_cells[x * cell_count + 3].find(string=True)
        time = a_cells[x * cell_count + 4].find(string=True)
        place = a_cells[x * cell_count + 5].find(string=True)
        home_href = a_cells[x * cell_count + 6].find('a', href=True)
        m = re.search("https://lhl-77\.ru/clubs/(\d+)/?", home_href['href'])
        is_home = int(m.group(1)) == int(club_id)
        home_team = home_href.string
        score = a_cells[x * cell_count + 7].find(string=True)
        away_href = a_cells[x * cell_count + 8].find('a', href=True)
        away_team = away_href.string

        uid = hash_of_game(club_id, tour, roundz)
        date_formatted = f'{date.replace("/", ".")} {time}'

        m = re.search("(\\d+):(\\d+)", score)
        sc_h = int(m.group(1))
        sc_a = int(m.group(2))

        g_recs.append(GameRecord(uid, date_formatted, place, home_team, away_team, sc_h, sc_a, is_home))
    # print(f'{uid} | {date_formatted} | {place} | {home_team} {sc_h} {sc_a} {away_team}')
    # print(json.dumps(g_recs, default = vars, ensure_ascii=False))
    return g_recs


def find_schedules(soup, club_id):
    table = soup.find('table', attrs={'class': 'table-standings--full-soccer'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    a_cells = table_body.find_all('td')
    cell_count = 10
    if len(a_cells) % cell_count != 0:
        return []
    rec_count = int(len(a_cells) / cell_count)
    g_recs = []
    for x in range(rec_count):
        tour = a_cells[x * cell_count + 0].find(string=True)
        roundz = a_cells[x * cell_count + 1].find(string=True)
        date = a_cells[x * cell_count + 3].find(string=True)
        day_of_week = a_cells[x * cell_count + 4].find(string=True)
        time = a_cells[x * cell_count + 5].find(string=True)
        place = a_cells[x * cell_count + 6].find(string=True)
        home_href = a_cells[x * cell_count + 7].find('a', href=True)
        m = re.search("https://lhl-77\.ru/clubs/(\d+)/?", home_href['href'])
        is_home = int(m.group(1)) == int(club_id)
        home_team = home_href.string

        score = a_cells[x * cell_count + 8].find(string=True)
        away_href = a_cells[x * cell_count + 9].find('a', href=True)
        away_team = away_href.string

        uid = hash_of_game(club_id, tour, roundz)
        date_formatted = f'{date.replace("/", ".")} {time}'

        m = re.search("(\\d+):(\\d+)", score)
        sc_h = int(m.group(1))
        sc_a = int(m.group(2))

        g_recs.append(GameRecord(uid, date_formatted, place, home_team, away_team, sc_h, sc_a, is_home))


    # print(f'{uid} | {date_formatted} | {place} | {home_team} {sc_h} {sc_a} {away_team}')
    # print(json.dumps(g_recs, default = vars, ensure_ascii=False))
    return g_recs


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--club', type=int, required=True, help='Club id in lhl')
    args_parser.add_argument('--season', type=int, required=True, help='Number of a season')
    args_parser.add_argument('--scope', type=Scope, required=False, choices=list(Scope),
                             help='Scope: all, schedule_only, score_only')

    args = args_parser.parse_args()
    club_id = args.club
    season_n = args.season
    scope = args.scope
    if scope is None:
        scope = Scope.ALL

    url_link = f'https://lhl-77.ru/clubs/{club_id}'

    # print(f'url {url_link}')

    response = requests.get(url_link)
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        content_ids = find_content_id(soup, season_n)

        result = {}

        scores = []
        if scope == Scope.ALL or scope == Scope.SCORE_ONLY:
            for content_id in content_ids:
                scores.extend(find_scores(soup, content_id, club_id))
            # print(scores)
            result["scores"] = sorted(scores, key=lambda game: datetime.strptime(game.date, '%d.%m.%Y %H:%M'))

        if scope == Scope.ALL or scope == Scope.SCHEDULE_ONLY:
            schedules = find_schedules(soup, club_id)
            result["schedule"] = sorted(schedules, key=lambda game: datetime.strptime(game.date, '%d.%m.%Y %H:%M'))

        print(json.dumps(result, default=vars, ensure_ascii=False, indent=True))
    else:
        print(f'Failed to retrieve the page. Status code: {response.status_code}')


main()
