import shelve
import game
import ui
import mob
import terrain
import render


def save_game():
    file = shelve.open('savegame', 'n')
    file['map'] = terrain.map
    # save player object index to find him when loading
    file['player_location'] = terrain.map.objects.index(game.player)
    file['alive'] = game.alive
    file['state'] = game.state
    file['turn'] = game.current_turn
    file['messages'] = ui.messages
    print 'game saved'
    file.close()


def load_game():
    file = shelve.open('savegame', 'r')
    terrain.map = file['map']
    terrain.map.init_fov_and_pathfinding()
    objindex = file['player_location']
    game.player = terrain.map.objects[objindex]
    game.alive = file['alive']
    game.state = file['state']
    game.current_turn = file['turn']
    ui.messages = file['messages']
    game.compute_fov()
    render.init()
    render.draw_all_tiles()
    print 'game loaded'
    file.close()
