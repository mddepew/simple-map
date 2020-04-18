import pygame
import pygame_gui
from simple_map import Game
import configparser
import csv
import os
import sys
from pathlib import Path

class TileSelectionDialog(pygame_gui.elements.UIPanel):
    def __init__(self, manager, tiles, pos, height):
        self.tiles = tiles
        self.tile_options = sorted(list(self.tiles.keys()))
        self.button_pad = 10
        self.buttons_per_page = 10
        self.tile_buttons = []
        self.tile_images = []
        self.selected_tile = 0
        self.active_page = 0
        self.page_max = len(self.tile_options) // self.buttons_per_page
        self.pos = pos
        pygame_gui.elements.UIPanel.__init__(self,
                                             starting_layer_height=10,
                                             relative_rect=pygame.Rect(self.pos, (300, height)),
                                             manager=manager)
        self.btnSave = pygame_gui.elements.UIButton(text='Save',
                                                    container=self,
                                                    relative_rect=pygame.Rect((10,20),(100,30)),
                                                    manager=manager)
        self.btnNext = pygame_gui.elements.UIButton(text='>',
                                                    container=self,
                                                    relative_rect=pygame.Rect((35,70),(25,30)),
                                                    manager=manager)
        self.btnPrev = pygame_gui.elements.UIButton(text='<',
                                                    container=self,
                                                    relative_rect=pygame.Rect((10,70),(25,30)),
                                                    manager=manager)
        for i in range(self.buttons_per_page):
            btnTile = pygame_gui.elements.UIButton(container=self,
                                                   text='tile%d'%i,
                                                   relative_rect=pygame.Rect((10,120 + i*(64+self.button_pad)),(64,64)),
                                                   manager=manager)
            btnTile.tile_index = i
            btnTile.img_name = self.tile_options[i]
            self.tile_buttons += [btnTile]

            imgTile = pygame_gui.elements.UIImage(container=self,
                                                  relative_rect=pygame.Rect((10,120 + i*(64+self.button_pad)),(64,64)),
                                                  image_surface=self.tiles[self.tile_options[i]],
                                                  manager=manager)
            self.tile_images += [imgTile]

        
    def get_selected_rect(self):
        return pygame.Rect((self.pos[0]+10+2,120 + self.selected_tile*(64+self.button_pad)+2),(64,64))
        
    def get_selected_image(self):
        return self.tile_buttons[self.selected_tile].img_name
    
    def update_images(self):
        for i in range(self.buttons_per_page):
            img_index = i + self.buttons_per_page*self.active_page
            if img_index < len(self.tile_options):
                self.tile_images[i].set_image(self.tiles[self.tile_options[img_index]])
                self.tile_buttons[i].img_name = self.tile_options[img_index]
            else:
                self.tile_images[i].set_image(self.tiles[self.tile_options[0]])
                self.tile_buttons[i].img_name = self.tile_options[0]


print('parsing config...')
conf = configparser.ConfigParser()
conf.read('config.ini')

map_margin = int(conf.get('Graphics', 'Map Margin'))
tile_padding = int(conf.get('Graphics', 'Tile Padding'))
tile_size = int(conf.get('Graphics', 'Tile Size'))
font_size = int(conf.get('Graphics', 'Font Size'))

conf_res = conf.get('Graphics', 'Resolution')

mapfile = input('map filename>').strip()
if Path(os.path.join('maps', mapfile)).exists():
    game_grid = Game.load_map(mapfile)
else:
    print('map not found, creating new map...')
    numrows = int(input('rows>'))
    numcols = int(input('cols>'))
    game_grid = []
    for _ in range(numrows):
        row = []
        for _ in range(numcols):
            row += ['grass']
        game_grid += [row]

display_width = int(conf_res.split('x')[0])
display_height = int(conf_res.split('x')[1])
print('spawning game instance...')
game = Game(server_hostname=None,
            server_port=None,
            display_width=display_width,
            display_height=display_height,
            map_margin=map_margin,
            tile_padding=tile_padding,
            tile_size=tile_size,
            font_size=font_size,
            refresh_period=1)

game.game_grid = game_grid
game.mapfile = mapfile

game.clock = pygame.time.Clock()
game.closed = False


            
    

tile_dialog = TileSelectionDialog(manager=game.ui_manager, tiles=game.tiles, pos=(display_width-300, 0), height=display_height)

closed = False

while not closed:
    time_delta = game.clock.tick(60)/1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            closed = True
        elif event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == tile_dialog.btnNext:
                    if tile_dialog.active_page < tile_dialog.page_max:
                        tile_dialog.active_page += 1
                        tile_dialog.update_images()
                elif event.ui_element == tile_dialog.btnPrev:
                    if tile_dialog.active_page > 0:
                        tile_dialog.active_page -= 1
                        tile_dialog.update_images()
                elif event.ui_element in tile_dialog.tile_buttons:
                    tile_dialog.selected_tile = event.ui_element.tile_index
                elif event.ui_element == tile_dialog.btnSave:
                    with open(os.path.join('maps',mapfile), 'w', newline='\n', encoding='utf-8') as fout:
                        writer = csv.writer(fout)
                        for row in game.game_grid:
                            writer.writerow(row)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and event.pos[0] < (display_width-300):
                pos_rc = game.x_y_to_row_col(*event.pos)
                if pos_rc is not None:
                    game.game_grid[pos_rc[0]][pos_rc[1]] = tile_dialog.get_selected_image()
            elif event.button in [4,5]:
                if event.pos[0] < (display_width-300):
                    game.process_event(event)
                    
        elif event.type == pygame.KEYDOWN:
            game.process_event(event)
                
        game.ui_manager.process_events(event)
    
    game.ui_manager.update(time_delta)
    
    game.display.fill(game.CLR_GREY)
    
    game.draw_tiles(game.display)
    
    game.ui_manager.draw_ui(game.display)
    
    pygame.draw.rect(game.display, (255,0,0), tile_dialog.get_selected_rect(), 3)
    
    pygame.display.update()
    game.clock.tick(60)

pygame.quit()
quit()