# Tetris desarrollado con PyGame
# Copyright (C) 2018 Recursos Python - recursospython.com.

from collections import OrderedDict
import random
from pygame import Rect
import pygame
import numpy as np


WINDOW_HEIGHT, WINDOW_WIDTH = 601, 500
GRID_HEIGHT, GRID_WIDTH = 600, 300
TILE_SIZE = 30

def remove_empty_columns(arr, _x_offset=0, _keep_counting=True):
    for colid, col in enumerate(arr.T):
        if col.max() == 0:
            if _keep_counting:
                _x_offset += 1
            # Remove the current column and try again.
            arr, _x_offset = remove_empty_columns(
                np.delete(arr, colid, 1), _x_offset, _keep_counting)
            break
        else:
            _keep_counting = False
    return arr, _x_offset

class BottomReached(Exception):
    pass

class TopReached(Exception):
    pass

class Block(pygame.sprite.Sprite):
    
    @staticmethod
    def collide(block, group):
        for other_block in group:
            if block == other_block:
                continue
            if pygame.sprite.collide_mask(block, other_block) is not None:
                return True
        return False
    
    def __init__(self):
        super().__init__()
        self.color = random.choice((
            (178,34,34),
            (255,215,0),
            (107,142,35),
            (0,100,0),
            (0,255,255),
            (127,255,212),
            (25,25,112),
            (148,0,211),
            (112,128,144)
        ))

        self.current = True
        self.struct = np.array(self.struct)

        if random.randint(0, 1):
            self.struct = np.rot90(self.struct)

        if random.randint(0, 1):
            # Giro en el eje x
            self.struct = np.flip(self.struct, 0)

        self._draw()
    
    def _draw(self, x=4, y=0):
        width = len(self.struct[0]) * TILE_SIZE
        height = len(self.struct) * TILE_SIZE
        self.image = pygame.surface.Surface([width, height])
        self.image.set_colorkey((0, 0, 0))
        # Posición y tamaño
        self.rect = Rect(0, 0, width, height)
        self.x = x
        self.y = y
        for y, row in enumerate(self.struct):
            for x, col in enumerate(row):
                if col:
                    pygame.draw.rect(
                        self.image,
                        self.color,
                        Rect(x*TILE_SIZE + 1, y*TILE_SIZE + 1,
                             TILE_SIZE - 2, TILE_SIZE - 2)
                    )
        self._create_mask()
    
    def redraw(self):
        self._draw(self.x, self.y)
    
    def _create_mask(self):
        self.mask = pygame.mask.from_surface(self.image)
    
    def initial_draw(self):
        raise NotImplementedError
    
    @property
    def group(self):
        return self.groups()[0]
    
    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value):
        self._x = value
        self.rect.left = value*TILE_SIZE
    
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value):
        self._y = value
        self.rect.top = value*TILE_SIZE
    
    def move_left(self, group):
        self.x -= 1
        if self.x < 0 or Block.collide(self, group):
            self.x += 1
    
    def move_right(self, group):
        self.x += 1
        if self.rect.right > GRID_WIDTH or Block.collide(self, group):
            self.x -= 1
    
    def move_down(self, group):
        self.y += 1
        if self.rect.bottom > GRID_HEIGHT or Block.collide(self, group):
            self.y -= 1
            self.current = False
            raise BottomReached
    
    def rotate(self, group):
        self.image = pygame.transform.rotate(self.image, 90)
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        self._create_mask()
        while self.rect.right > GRID_WIDTH:
            self.x -= 1
        while self.rect.left < 0:
            self.x += 1
        while self.rect.bottom > GRID_HEIGHT:
            self.y -= 1
        while True:
            if not Block.collide(self, group):
                break
            self.y -= 1
        self.struct = np.rot90(self.struct)
    
    def update(self):
        if self.current:
            self.move_down()

class SquareBlock(Block):
    struct = (
        (1, 1),
        (1, 1)
    )

class TBlock(Block):
    struct = (
        (1, 1, 1),
        (0, 1, 0)
    )

class LineBlock(Block):
    struct = (
        (1,),
        (1,),
        (1,),
        (1,)
    )

class LBlock(Block):
    struct = (
        (1, 1),
        (1, 0),
        (1, 0),
    )

class L2Block(Block):
    struct = (
        (1, 0),
        (1, 0),
        (1, 1),
    )

class ZBlock(Block):
    struct = (
        (0, 1),
        (1, 1),
        (1, 0),
    )

class Z2Block(Block):
    struct = (
        (1, 0),
        (1, 1),
        (0, 1),
    )

class BlocksGroup(pygame.sprite.OrderedUpdates):
    
    @staticmethod
    def get_random_block():
        return random.choice(
            (SquareBlock, TBlock, LineBlock, LBlock, L2Block, ZBlock, Z2Block))()
    
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self._reset_grid()
        self._ignore_next_stop = False
        self.score = 0
        self.next_block = None
        self.stop_moving_current_block()
        self._create_new_block()
    
    def _check_line_completion(self):
        # Empieza a comprobar desde abajo
        for i, row in enumerate(self.grid[::-1]):
            if all(row):
                self.score += 5
                affected_blocks = list(
                    OrderedDict.fromkeys(self.grid[-1 - i]))
                
                for block, y_offset in affected_blocks:
                    block.struct = np.delete(block.struct, y_offset, 0)
                    if block.struct.any():
                        block.struct, x_offset = \
                            remove_empty_columns(block.struct)
                        block.x += x_offset
                        block.redraw()
                    else:
                        self.remove(block)
                
                for block in self:
                    if block.current:
                        continue
                    while True:
                        try:
                            block.move_down(self)
                        except BottomReached:
                            break
                
                self.update_grid()
                self._check_line_completion()
                break
    
    def _reset_grid(self):
        self.grid = [[0 for _ in range(10)] for _ in range(20)]
    
    def _create_new_block(self):
        new_block = self.next_block or BlocksGroup.get_random_block()
        if Block.collide(new_block, self):
            raise TopReached
        self.add(new_block)
        self.next_block = BlocksGroup.get_random_block()
        self.update_grid()
        self._check_line_completion()
    
    def update_grid(self):
        self._reset_grid()
        for block in self:
            for y_offset, row in enumerate(block.struct):
                for x_offset, digit in enumerate(row):
                    if digit == 0:
                        continue
                    rowid = block.y + y_offset
                    colid = block.x + x_offset
                    self.grid[rowid][colid] = (block, y_offset)
    
    @property
    def current_block(self):
        return self.sprites()[-1]
    
    def update_current_block(self):
        try:
            self.current_block.move_down(self)
        except BottomReached:
            self.stop_moving_current_block()
            self._create_new_block()
        else:
            self.update_grid()
    
    def move_current_block(self):
        if self._current_block_movement_heading is None:
            return
        action = {
            pygame.K_DOWN: self.current_block.move_down,
            pygame.K_LEFT: self.current_block.move_left,
            pygame.K_RIGHT: self.current_block.move_right
        }
        
        try:
            action[self._current_block_movement_heading](self)
        except BottomReached:
            self.stop_moving_current_block()
            self._create_new_block()
        else:
            self.update_grid()
    
    def start_moving_current_block(self, key):
        if self._current_block_movement_heading is not None:
            self._ignore_next_stop = True
        self._current_block_movement_heading = key
    
    def stop_moving_current_block(self):
        if self._ignore_next_stop:
            self._ignore_next_stop = False
        else:
            self._current_block_movement_heading = None
    
    def rotate_current_block(self):
        # Previene la rotación de SquareBlocks
        if not isinstance(self.current_block, SquareBlock):
            self.current_block.rotate(self)
            self.update_grid()

def draw_grid(background):
    grid_color = 50, 50, 50
    # Líneas verticales
    for i in range(11):
        x = TILE_SIZE * i
        pygame.draw.line(
            background, grid_color, (x, 0), (x, GRID_HEIGHT)
        )
    # Líneas horizontales
    for i in range(21):
        y = TILE_SIZE * i
        pygame.draw.line(
            background, grid_color, (0, y), (GRID_WIDTH, y)
        )

def draw_centered_surface(screen, surface, y):
    screen.blit(surface, (400 - surface.get_width()/2, y))

def main():
    pygame.init()
    pygame.display.set_caption("TETRIS")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    run = True
    paused = False
    game_over = False
    # Crea el background
    background = pygame.Surface(screen.get_size())
    rbgcolor = (0, 0, 0)
    background.fill(rbgcolor)
    # Dibuja la cuadrícula encima del background
    draw_grid(background)
    background = background.convert()
    
    try:
        font = pygame.font.Font("NotoSans-Regular.ttf", 20)
    except OSError:
        pass

    next_block_text = font.render(
        "Próxima figura:", True, (255, 255, 255), rbgcolor)
    score_msg_text = font.render(
        "Puntos:", True, (255, 255, 255), rbgcolor)
    instructions_text = font.render(
        "Pausa: Espacio", True, (255, 255, 255), rbgcolor)
    reset_text = font.render(
        "Reiniciar: 'r'", True, (255, 255, 255), rbgcolor)
    quit_text = font.render(
        "Quitar: Escape", True, (255, 255, 255), rbgcolor)
    game_over_text = font.render(
        "GAME OVER", True, (255,99,71), rbgcolor)
    
    MOVEMENT_KEYS = pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN
    EVENT_UPDATE_CURRENT_BLOCK = pygame.USEREVENT + 1
    EVENT_MOVE_CURRENT_BLOCK = pygame.USEREVENT + 2
    pygame.time.set_timer(EVENT_UPDATE_CURRENT_BLOCK, 1000)
    pygame.time.set_timer(EVENT_MOVE_CURRENT_BLOCK, 100)
    
    blocks = BlocksGroup()
    
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            elif event.type == pygame.KEYUP:
                if not paused and not game_over:
                    if event.key in MOVEMENT_KEYS:
                        blocks.stop_moving_current_block()
                    elif event.key == pygame.K_UP:
                        blocks.rotate_current_block()
                if event.key == pygame.K_SPACE:
                    paused = not paused
            
            # Deja de mover los bloques si se pausa o se termina
            if game_over or paused:
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key in MOVEMENT_KEYS:
                    blocks.start_moving_current_block(event.key)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit()

            try:
                if event.type == EVENT_UPDATE_CURRENT_BLOCK:
                    blocks.update_current_block()
                elif event.type == EVENT_MOVE_CURRENT_BLOCK:
                    blocks.move_current_block()
            except TopReached:
                game_over = True
        
        # Dibuja la cuadrícula y el background
        screen.blit(background, (0, 0))
        # Dibuja los bloques
        blocks.draw(screen)
        # Barra lateral con información
        draw_centered_surface(screen, next_block_text, 50)
        draw_centered_surface(screen, blocks.next_block.image, 100)
        draw_centered_surface(screen, score_msg_text, 230)
        score_text = font.render(
            str(blocks.score), True, (255, 255, 255), rbgcolor)
        draw_centered_surface(screen, score_text, 260)
        draw_centered_surface(screen, instructions_text, 290)
        draw_centered_surface(screen, reset_text, 330)
        draw_centered_surface(screen, quit_text, 370)
        if game_over:
            draw_centered_surface(screen, game_over_text, 410)
        pygame.display.flip()
    
    pygame.quit()
if __name__ == "__main__":
    main()
