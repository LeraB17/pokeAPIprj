from app import app
from settings import *
from datetime import date
from io import StringIO
import requests, sys, json, ftplib
import unittest
import flask_unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.webdriver import WebDriver

from api import default_limit


class TestApiMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ftp = ftplib.FTP(host=FTP_HOST)
        cls.ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)

    @classmethod
    def tearDownClass(cls):
        cls.ftp.quit() 

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def tearDown(self):
        pass 

    def test_get_pokemon_info(self):
        response = self.client.get('/api/pokemon/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual([data['id'], data['name'], data['hp'], data['attack'], data['defense']],
                         [1, 'bulbasaur', 45, 49, 49])

    def test_get_pokemon_list(self):
        # без параметров
        response = self.client.get('/api/pokemon/list')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data_without_params = json.loads(response.data)
        self.assertEqual(data_without_params['pages'], int(1292 / default_limit) + int(1292 % default_limit > 0))
        self.assertEqual(len(data_without_params['pokemons']), default_limit)
        self.assertEqual([poke['id'] for poke in data_without_params['pokemons']], list(range(1, default_limit + 1)))
        # с номером страницы
        response = self.client.get('/api/pokemon/list?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data_with_page = json.loads(response.data)
        self.assertEqual(data_with_page['pages'], int(1292 / default_limit) + int(1292 % default_limit > 0))
        self.assertEqual(len(data_with_page['pokemons']), default_limit)
        self.assertEqual([poke['id'] for poke in data_with_page['pokemons']], list(range(1 + default_limit, 2 * default_limit + 1)))
        # с изменённым лимитом на страницу
        test_limit = 20
        response = self.client.get(f'/api/pokemon/list?limit={test_limit}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data_with_limit = json.loads(response.data)
        self.assertEqual(data_with_limit['pages'], int(1292 / test_limit) + int(1292 % test_limit > 0))
        self.assertEqual(len(data_with_limit['pokemons']), test_limit)
        self.assertEqual([poke['id'] for poke in data_with_limit['pokemons']], list(range(1, test_limit + 1)))
        # со строкой поиска
        search_string1 = 'saur'
        response = self.client.get(f'/api/pokemon/list?q={search_string1}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data_with_search = json.loads(response.data)
        self.assertTrue(len(data_with_search['pokemons']) <= default_limit)
        self.assertEqual([poke['name'] for poke in data_with_search['pokemons'][:3]], ['bulbasaur', 'ivysaur', 'venusaur'])
        # если ничего не нашлось
        search_string2 = 'saaaaaur'
        response = self.client.get(f'/api/pokemon/list?q={search_string2}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data_with_search = json.loads(response.data)
        self.assertEqual(len(data_with_search['pokemons']), 0)
        # поиск + страница
        search_string = 'sa'
        response = self.client.get(f'/api/pokemon/list?page=2&q={search_string}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data_with_search = json.loads(response.data)
        self.assertTrue(len(data_with_search['pokemons']) <= default_limit)
        self.assertEqual(data_with_search['pokemons'][0]['name'], 'pansage')

    def test_get_random_pokemon(self):
        response = self.client.get('/api/pokemon/random')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        response2 = requests.get('https://pokeapi.co/api/v2/pokemon/?limit=1')
        data2 = response2.json() if response2.status_code == 200 else {}

        self.assertEqual(type(data['id']), type(1))
        self.assertTrue(0 < data['id'] < data2['count'])

    def test_fight(self):
        id_select = 1
        id_vs = 2
        response = self.client.get(f'/api/fight?id_select={id_select}&id_vs={id_vs}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        response1 = self.client.get(f'/api/pokemon/{id_select}')
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.content_type, 'application/json')
        data1 = json.loads(response1.data)

        response2 = self.client.get(f'/api/pokemon/{id_vs}')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.content_type, 'application/json')
        data2 = json.loads(response2.data)

        self.assertDictEqual(data['select_pokemon'], data1)
        self.assertDictEqual(data['vs_pokemon'], data2)
        self.assertEqual(data['select_pokemon']['name'], 'bulbasaur')
        self.assertEqual(data['vs_pokemon']['name'], 'ivysaur')
    
    def test_attack(self):
        select_number = 5
        
        select_pokemon = 1
        select_pokemon_hp = 45
        select_pokemon_attack = 49
        vs_pokemon = 2
        vs_pokemon_hp = 60
        vs_pokemon_attack = 62

        response = self.client.post(f'/api/fight/{select_number}', data=json.dumps({
            'select_pokemon': {
                'id': select_pokemon,
                'hp': select_pokemon_hp,
                'attack': select_pokemon_attack,
            },
            'vs_pokemon': {
                'id': vs_pokemon,
                'hp': vs_pokemon_hp,
                'attack': vs_pokemon_attack,
            },
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        
        round = data['round']
        
        if round[0]['number'] % 2 == round[1]['number'] % 2:
            self.assertEqual(round[1]['hp'], vs_pokemon_hp - select_pokemon_attack)
        else:
            self.assertEqual(round[0]['hp'], select_pokemon_hp - vs_pokemon_attack)
            
        if round[0]['hp'] <= 0 or round[1]['hp'] <= 0:
            self.assertTrue(round[2] != None)

    def test_fast_fight(self):
        select_pokemon = 1
        vs_pokemon = 2

        response = self.client.get(f'/api/fight/fast?id_select={select_pokemon}&id_vs={vs_pokemon}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        self.assertTrue(data['select_pokemon']['hp'] <= 0 or data['vs_pokemon']['hp'] <= 0)
        if data['select_pokemon']['hp'] > 0:
            self.assertTrue(data['select_pokemon']['id'] == data['winner'])
        else:
            self.assertTrue(data['vs_pokemon']['id'] == data['winner'])
            
    def test_save_info(self):
        pokemon_id = 1
        response = self.client.post(f'/api/save-info/{pokemon_id}')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        pokemon_name = 'bulbasaur'
        self.assertEqual(data['pokemon_name'], pokemon_name)

        folder_name = str(date.today()).replace('-', '').strip()
        self.assertTrue(folder_name in self.ftp.nlst())
        self.ftp.cwd(folder_name)       
        self.assertTrue(f'{pokemon_name}.md' in self.ftp.nlst())

        tmp = sys.stdout
        res = StringIO()
        sys.stdout = res
        self.ftp.retrlines(f'RETR {pokemon_name}.md')
        sys.stdout = tmp
        text = res.getvalue()
        self.assertTrue(f'# Name: {pokemon_name}' in text)



class TestBySelenium(flask_unittest.LiveTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True  

    def tearDown(self):
        pass 

    def test_list_page(self):
        self.selenium.get(f'http://{APP_IP}:{APP_PORT}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        response = self.app.get('/api/pokemon/list?page=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        cards = self.selenium.find_elements(By.CLASS_NAME, "pokemon-card")
        self.assertTrue(len(cards) == len(data['pokemons']))

    def test_pokemon_page(self):
        pokemon = 'bulbasaur'
        self.selenium.get(f'http://{APP_IP}:{APP_PORT}/pokemon/{pokemon}')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        response = self.app.get(f'/api/pokemon/{pokemon}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        pokemon_name = self.selenium.find_element(By.TAG_NAME, "h2").text
        stats = self.selenium.find_element(By.CLASS_NAME, 'stats').find_elements(By.TAG_NAME, "div")
        pokemon_stats = [pokemon_div.text for pokemon_div in stats]

        self.assertEqual(pokemon_name, data['name'])
        self.assertEqual(pokemon_stats, [
            f"hp: {data['hp']}", f"attack: {data['attack']}", f"defense: {data['defense']}", f"speed: {data['speed']}"
        ])

    def test_pokemon_search(self):
        self.selenium.get(f'http://{APP_IP}:{APP_PORT}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        search_string = 'saur'
        search_input = self.selenium.find_element(By.NAME, "search_string")
        search_input.send_keys(search_string)
        self.selenium.find_element(By.XPATH, '//button[text()="Search"]').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )

        response = self.app.get(f'/api/pokemon/list?q={search_string}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        cards = self.selenium.find_elements(By.CLASS_NAME, "pokemon-card")
        self.assertTrue(len(cards) == len(data['pokemons']))

    def test_attack(self):
        self.selenium.get(f'http://{APP_IP}:{APP_PORT}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        self.selenium.find_element(By.XPATH, '//button[text()="Select"]').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        entered_number_input = self.selenium.find_element(By.NAME, "entered_number")
        number = 5
        entered_number_input.send_keys(number)
        self.selenium.find_element(By.XPATH, '//button[text()="Enter"]').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        table = self.selenium.find_element(By.TAG_NAME, "table")
        td1 = table.find_element(By.TAG_NAME, "td")
        self.assertTrue(td1.text == str(number))


if __name__ == '__main__':
    suite = flask_unittest.LiveTestSuite(app)
    suite.addTest(unittest.makeSuite(TestApiMethods))
    suite.addTest(unittest.makeSuite(TestBySelenium))
    unittest.TextTestRunner(verbosity=2).run(suite)
