#! /usr/bin/python3
# Print games for a club in a season in JSON format

import argparse, requests
from bs4 import BeautifulSoup

def find_content_id(soup, season_n):
	panel_headings = soup.find_all(class_='panel-heading')
	for el in panel_headings:
		sub_header = el.find_all(class_='game-result__subheader')[0]
		if f'{season_n}-й' in sub_header.text:
			return int(el.get('id').replace("heading", ""))

def main():
	args_parser = argparse.ArgumentParser()
	args_parser.add_argument('--club', type=int, required=True, help='Club id in lhl')
	args_parser.add_argument('--season', type=int, required=True, help='Number of a season')

	args = args_parser.parse_args()
	club_id = args.club
	season_n = args.season

	print(f'Club_id {club_id}, season_n {season_n}')

	url_link =f'https://lhl-77.ru/clubs/{club_id}'

	print(f'url {url_link}')

	response = requests.get(url_link)
	if response.status_code == 200:
		# Parse the HTML content
		soup = BeautifulSoup(response.text, 'html.parser')

		content_id = find_content_id(soup, season_n)

		print(f'CONTENT_ID - {content_id}')

		games_panel = soup.find(id=f'collapse{content_id}')

		print("\n\n\nGAME RESULTS:\n")
		print(games_panel.find_all(class_='table-responsive'))


		print("\n\n\nGAME STANDINGS:\n")
		print(soup.find_all(class_='table-standings'))
	else:
		print(f'Failed to retrieve the page. Status code: {response.status_code}')

main()