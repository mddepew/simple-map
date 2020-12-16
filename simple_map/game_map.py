import pygame
import glob
import os
import socket
import json
import pkg_resources.py2_warn
import configparser
import csv
import pygame_gui
import copy

class TokenSelectionDialog(pygame_gui.elements.UIWindow):
    def __init__(self, manager, row, col, token_images):
        token_options = sorted(list(token_images.keys()))
        pygame_gui.elements.UIWindow.__init__(self,
                                              rect=pygame.Rect((350, 275), (300, 500)),
                                              manager=manager)
        self.lblName = pygame_gui.elements.UILabel(container=self,
                                                   relative_rect=pygame.Rect((10,10),(100,30)),
                                                   manager=manager,
                                                   text='Name:')
        self.txtName = pygame_gui.elements.UITextEntryLine(container=self,
                                                           relative_rect=pygame.Rect((10,40),(100,50)),
                                                           manager=manager)
        self.cmbImg = pygame_gui.elements.UIDropDownMenu(options_list=token_options,
                                                         starting_option=token_options[0],
                                                         container=self,
                                                         relative_rect=pygame.Rect((10,90),(250,50)),
                                                         manager=manager)
        self.imgToken = pygame_gui.elements.UIImage(container=self,
                                                    relative_rect=pygame.Rect((10,150),(64,64)),
                                                    image_surface=token_images[token_options[0]],
                                                    manager=manager)
        self.btnOk = pygame_gui.elements.UIButton(text='OK',
                                                  container=self,
                                                  relative_rect=pygame.Rect((10,224),(100,50)),
                                                  manager=manager)
        self.row = row
        self.col = col
        self.set_blocking(True)
        self.is_modal = True

class Game:
    CLR_BLACK = (0, 0, 0)
    CLR_WHITE = (255, 255, 255)
    CLR_GREY = (200, 200, 200)
    
    def __init__(self,
                 server_hostname,
                 server_port,
                 display_width,
                 display_height,
                 map_margin,
                 tile_padding,
                 tile_size,
                 font_size,
                 refresh_period):
        self.map_margin = map_margin
        self.tile_padding = tile_padding
        self.tile_size = tile_size
        self.font_size = font_size
        self.display_width = display_width
        self.display_height = display_height
        self.refresh_period = refresh_period
        
        self.default_token = 'black_circle'
        self.default_tile = 'white'
        
        self.game_grid = None
        self.tokens = {}
        self.selected_token = None
        
        self.load_images()
        
        self.scaled_tiles = {}
        self.scaled_token_images = {}
        
        self.view_offset = (0,0)
        
        if server_hostname is not None and server_port is not None:
            self.server_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_con.connect((server_hostname, server_port))
        else:
            self.server_con = None
        
        self.mapfile = None
        if self.server_con is not None:
            self.update_map()
        
        print('initializing game engine')
        self.display = pygame.display.set_mode((display_width,display_height))
        pygame.display.set_caption('Simple Map')
        pygame.init()
        self.font = pygame.font.Font('arial.ttf',self.font_size)
        self.ui_manager = pygame_gui.UIManager((self.display_width, self.display_height))
        
        self.token_dialog = None
    
    def __del__(self):
        if self.server_con is not None:
            self.server_con.close()
    
    def load_images(self):
        print('loading images...')
        self.tiles = {}
        
        for img_file in glob.glob('tiles/*.png'):
            tile_name = os.path.splitext(os.path.basename(img_file))[0]
            self.tiles[tile_name] = pygame.image.load(img_file)
            
        self.token_images = {}

        for img_file in glob.glob('tokens/*.png'):
            token_name = os.path.splitext(os.path.basename(img_file))[0]
            self.token_images[token_name] = pygame.image.load(img_file)
            
    def rescale_assets(self):
        #Rescale font, this is the lazy way
        self.font = pygame.font.Font('arial.ttf',self.font_size)
        #clear scaled tile and token caches
        self.scaled_tiles = {}
        self.scaled_token_images = {}
    
    def get_scaled_token(self, token_name):
        if token_name in self.scaled_token_images:
            return self.scaled_token_images[token_name]
        elif token_name in self.token_images:
            if token_name[-2:] == '2x':
                self.scaled_token_images[token_name] = pygame.transform.scale(self.token_images[token_name],
                                                                              (self.tile_size*2,self.tile_size*2))
            else:
                self.scaled_token_images[token_name] = pygame.transform.scale(self.token_images[token_name],
                                                                              (self.tile_size,self.tile_size))
            return self.scaled_token_images[token_name]
        else:
            print('Token with name "%s" not found.' % token_name)
            return self.get_scaled_token(self.default_token)

    def get_scaled_tile(self, tile_name):
        if tile_name in self.scaled_tiles:
            return self.scaled_tiles[tile_name]
        elif tile_name in self.tiles:
            self.scaled_tiles[tile_name] = pygame.transform.scale(self.tiles[tile_name],
                                                                 (self.tile_size,self.tile_size))
            return self.scaled_tiles[tile_name]
        else:
            print('Tile with name "%s" not found.' % tile_name)
            return self.get_scaled_tile(self.default_tile)

    def x_y_to_row_col(self, x, y):
        for row in range(len(self.game_grid)):
            for col in range(len(self.game_grid[row])):
                tile_x, tile_y = self.row_col_to_x_y(row, col)
                if tile_x < x < (tile_x + self.tile_size) and tile_y < y < (tile_y + self.tile_size):
                    return (row, col)
        return None

    def row_col_to_x_y(self, row, col):
        y_pos = self.map_margin + row*(self.tile_size + self.tile_padding)
        x_pos = self.map_margin + col*(self.tile_size + self.tile_padding)
        return (x_pos+self.view_offset[0],y_pos+self.view_offset[1])

    def draw_tokens(self):
        for name,token in self.tokens.items():
            if token['row'] is not None and token['col'] is not None:
                x,y = self.row_col_to_x_y(token['row'], token['col'])
                self.display.blit(self.get_scaled_token(token['img']),(x,y))
                # now print the text
                text_surface = self.font.render(name, True, (0, 0, 255))
                self.display.blit(text_surface, dest=(x,y+self.tile_size-self.font_size))
                if name == self.selected_token:
                    if token['img'][-2:] == '2x':
                        pygame.draw.rect(self.display, (255,0,0), pygame.Rect(x,y, self.tile_size*2, self.tile_size*2), 3)
                    else:
                        pygame.draw.rect(self.display, (255,0,0), pygame.Rect(x,y, self.tile_size, self.tile_size), 3)

    def draw_tiles(self, display):
        for row in range(len(self.game_grid)):
            for col in range(len(self.game_grid[row])):
                x_pos, y_pos = self.row_col_to_x_y(row, col)
                display.blit(self.get_scaled_tile(self.game_grid[row][col]), (x_pos,y_pos))

    def update_tokens(self):
        self.server_con.sendall(json.dumps({'op':'get', 'arg':'tokens'}).encode())
        try:
            resp_len_str = self.server_con.recv(8).decode()
            resp_len = int(resp_len_str)
            data = ''
            while len(data) < resp_len:
                data += self.server_con.recv(resp_len - len(data)).decode()
            try:
                self.tokens = json.loads(data)
            except json.decoder.JSONDecodeError:
                print('Failed to parse tokens')
        except ValueError:
            print('Failed to parse response length')
    
    @staticmethod
    def load_map(mapfile):
        game_grid = []
        with open(os.path.join('maps',mapfile), 'r') as fin:
            reader = csv.reader(fin)
            for row in reader:
                game_grid += [row]
        return game_grid
        
    def update_map(self):
        self.server_con.sendall(json.dumps({'op':'get', 'arg':'map'}).encode())
        resp_len = int(self.server_con.recv(8).decode())
        data = self.server_con.recv(resp_len)
        mapfile = json.loads(data.decode())
        if mapfile != self.mapfile:
            self.game_grid = self.load_map(mapfile)
            self.mapfile = mapfile

    def move_token(self,name, row, col):
        token_to_move = self.tokens[name]
        token_to_move['name'] = name
        token_to_move['row'] = row
        token_to_move['col'] = col
        self.server_con.sendall(json.dumps({'op':'set', 'arg':'place_token', 'data':token_to_move}).encode())
        resp_len = int(self.server_con.recv(8).decode())
        data = self.server_con.recv(resp_len)
        if data.decode() != 'ack':
            print('Move not acknowledged by server')
    
    def process_event(self, event):
        if self.token_dialog is not None:
            token_window_open = self.token_dialog.is_modal
        else:
            token_window_open = False
        if event.type == pygame.QUIT:
            self.closed = True

        ############################
        # if any mouse button is pressed
        if event.type == pygame.MOUSEBUTTONDOWN and not token_window_open:
            if event.button == 1:
                pos_rc = self.x_y_to_row_col(*event.pos)
                if pos_rc is not None:
                    if self.selected_token is not None:
                        self.move_token(self.selected_token, pos_rc[0], pos_rc[1])
                        self.selected_token = None
                    elif pygame.key.get_pressed()[pygame.K_RCTRL] or pygame.key.get_pressed()[pygame.K_LCTRL]:
                        pending_token_r, pending_token_c = pos_rc
                        self.token_dialog = TokenSelectionDialog(self.ui_manager,
                                                                 row=pos_rc[0],
                                                                 col=pos_rc[1],
                                                                 token_images=self.token_images)
                    else:
                        for token_name, token in self.tokens.items():
                            if (token['row'], token['col']) == pos_rc:
                                self.selected_token = token_name
                                break
            elif event.button == 5:
                if self.tile_size > 5:
                    self.tile_size -= 5
                    self.font_size -= 1
                    self.rescale_assets()
            elif event.button == 4:
                self.tile_size += 5
                self.font_size += 1
                self.rescale_assets()
            
        elif event.type == pygame.KEYDOWN and not token_window_open:
            if event.key == pygame.K_DELETE:
                if self.selected_token is not None:
                    self.move_token(self.selected_token, None, None)
                    self.selected_token = None
            elif event.key == pygame.K_RIGHT:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.view_offset = (self.view_offset[0]-(self.tile_size+self.tile_padding)*10,
                                        self.view_offset[1])
                else:
                    self.view_offset = (self.view_offset[0]-(self.tile_size+self.tile_padding),
                                        self.view_offset[1])
            elif event.key == pygame.K_LEFT:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.view_offset = (self.view_offset[0]+(self.tile_size+self.tile_padding)*10,
                                        self.view_offset[1])
                else:
                    self.view_offset = (self.view_offset[0]+(self.tile_size+self.tile_padding),
                                        self.view_offset[1])
            elif event.key == pygame.K_DOWN:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.view_offset = (self.view_offset[0],
                                        self.view_offset[1]-(self.tile_size+self.tile_padding)*10)
                else:
                    self.view_offset = (self.view_offset[0],
                                        self.view_offset[1]-(self.tile_size+self.tile_padding))
            elif event.key == pygame.K_UP:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.view_offset = (self.view_offset[0],
                                        self.view_offset[1]+(self.tile_size+self.tile_padding)*10)
                else:
                    self.view_offset = (self.view_offset[0],
                                        self.view_offset[1]+(self.tile_size+self.tile_padding))
            elif event.key == pygame.K_MINUS:
                if self.tile_size > 5:
                    self.tile_size -= 5
                    self.font_size -= 1
                    self.rescale_assets()
            elif event.key == pygame.K_EQUALS:
                self.tile_size += 5
                self.font_size += 1
                self.rescale_assets()
        elif event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if self.token_dialog is not None:
                    if event.ui_element == self.token_dialog.btnOk:
                        token_name = self.token_dialog.txtName.text
                        token_image = self.token_dialog.cmbImg.selected_option
                        self.tokens[token_name] = {'row':1, 'col':1, 'img':token_image}
                        self.move_token(token_name, self.token_dialog.row, self.token_dialog.col)
                        self.token_dialog.is_modal = False
                        self.token_dialog.kill()
            elif event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if self.token_dialog is not None:
                    if event.ui_element == self.token_dialog.cmbImg:
                        self.token_dialog.imgToken.set_image(self.token_images[event.text])
    
    def game_loop(self):
        self.clock = pygame.time.Clock()

        self.closed = False
        frame_count = 0
        
        while not self.closed:
            frame_count += 1
            time_delta = self.clock.tick(60)/1000.0
            
            for event in pygame.event.get():
                self.process_event(event)
                self.ui_manager.process_events(event)
            
            self.ui_manager.update(time_delta)
            if frame_count >= self.refresh_period:
                self.update_map()
                self.update_tokens()
                frame_count = 0
            
            self.display.fill(self.CLR_GREY)
            
            self.draw_tiles(self.display)
            
            self.draw_tokens()
            
            
            self.ui_manager.draw_ui(self.display)
            
            
            pygame.display.update()
            self.clock.tick(60)

        pygame.quit()
        quit()
