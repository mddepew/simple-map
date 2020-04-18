from simple_map import Game
import configparser

print('parsing config...')
conf = configparser.ConfigParser()
conf.read('config.ini')

map_margin = int(conf.get('Graphics', 'Map Margin'))
tile_padding = int(conf.get('Graphics', 'Tile Padding'))
tile_size = int(conf.get('Graphics', 'Tile Size'))
font_size = int(conf.get('Graphics', 'Font Size'))

host = conf.get('Server', 'Hostname')
port = int(conf.get('Server', 'Port'))
refresh_period = int(conf.get('Server', 'Refresh Period'))

conf_res = conf.get('Graphics', 'Resolution')

display_width = int(conf_res.split('x')[0])
display_height = int(conf_res.split('x')[1])
print('spawning game instance...')
game = Game(server_hostname=host,
                       server_port=port,
                       display_width=display_width,
                       display_height=display_height,
                       map_margin=map_margin,
                       tile_padding=tile_padding,
                       tile_size=tile_size,
                       font_size=font_size,
                       refresh_period=refresh_period)

game.game_loop()