from PythonClientAPI.game.PointUtils import *
from PythonClientAPI.game.Entities import FriendlyUnit, EnemyUnit, Tile
from PythonClientAPI.game.Enums import Team
from PythonClientAPI.game.World import World
from PythonClientAPI.game.TileUtils import TileUtils
from PythonClientAPI.game.PathFinder import PathFinder


class PlayerAI:
    def __init__(self):
        ''' Initialize! '''
        self.turn_count = 0             # game turn count
        self.rec_len = 10
        self.units_taken = 0
        self.LEFT = 0
        self.RIGHT = 0
        self.TOP = 0
        self.BOTTOM = 0
        self.target_list = []
        self.direction = None
        self.init_target = (0,0)
        self.ind = 0
        self.dir_list = []
        self.first_move = (0,0)
        self.second_move = (0,0)
        self.square = ({"south": (-10, 0), "north": (10, 0)}, {"east": (0, 10), "west": (0, -10)})
        self.target = None
        self.is_init = True


    def calc_units_til_fin(self, _rec_len):
        return (_rec_len*2+4) - self.units_taken

    def compute_enemy_distance(self,enemy_units,world,friendly_unit):
        enemy_distance = {}
        for enemy in enemy_units:
            enemy_distance[enemy.uuid] = min(
                [world.path.get_taxi_cab_distance(enemy.position, body_position) for body_position in
                 friendly_unit.snake])
        return enemy_distance

    def compare_distance(self, world, enemy_units, friendly_unit):
        # go all the way to right until REC_LEN is reached
        units_til_fin = self.calc_units_til_fin(self.rec_len)

        enemy_distance = self.compute_enemy_distance(enemy_units, world, friendly_unit)

        new_rec_len = self.rec_len
        for distance in enemy_distance:
            if distance == units_til_fin:
                # get its max len with this distance
                try_rec_len = new_rec_len
                while try_rec_len > 0:
                    try_rec_len -= 1
                    # recalculate units_til_fin
                    units_til_fin = self.calc_units_til_fin(try_rec_len)
                    if units_til_fin < distance:
                        break

                if try_rec_len < new_rec_len:
                    new_rec_len = try_rec_len

        self.rec_len = new_rec_len

    def dir_move(self, friendly_unit):
        if self.direction == "right":
            return (friendly_unit.position[0]+1, friendly_unit.position[1])
        elif self.direction == "up":
            return (friendly_unit.position[0], friendly_unit.position[1]-1)
        elif self.direction == "left":
            return (friendly_unit.position[0]-1, friendly_unit.position[1])
        elif self.direction == "down":
            return (friendly_unit.position[0], friendly_unit.position[1]+1)

    def update_dir(self, friendly_unit):
        if friendly_unit.position == (3, 3):
            self.first_move = (3,4)
            self.second_move = (4,4)
            self.dir_list = ["up", "left", "down"]
            self.target_list.extend([(4, 2),(3,2), (3,self.TOP),(self.LEFT, self.TOP), (self.LEFT, 4)])
            self.direction = "right"
        elif friendly_unit.position == (26,3):
            self.first_move = (26,4)
            self.second_move = (25,4)
            self.dir_list = ["up", "right", "down"]
            self.target_list.extend([(25, 2),(26,2),(26,self.TOP),(self.RIGHT, self.TOP), (self.RIGHT, 4)])
            self.direction = "left"
        elif friendly_unit.position == (3,26):
            self.first_move = (3,25)
            self.second_move = (4, 25)
            self.dir_list = ["down", "left", "up"]
            self.target_list.extend([(4, 27), (3,27), (3,self.BOTTOM), (self.LEFT, self.BOTTOM), (self.LEFT, 25)])
            self.direction = "right"
        elif friendly_unit.position == (26,26):
            self.first_move = (26,25)
            self.second_move = (25,25)
            self.dir_list = ["down", "right", "up"]
            self.target_list.extend([(25,27), (26,27), (26,28), (self.RIGHT, self.BOTTOM), (self.RIGHT, 25)])
            self.direction = "left"


    def rec_2_move(self, friendly_unit):
        # print("f:")
        print(friendly_unit.position)
        if friendly_unit.position == self.target_list[self.ind]:
            self.ind += 1
            self.init_target = self.target_list[self.ind]

    def change_dir(self, dir_list):
        if self.units_taken == self.rec_len:
            self.direction = dir_list[0]
        elif self.units_taken == self.rec_len + 3:
            self.direction = dir_list[1]
        elif self.units_taken == 2*self.rec_len + 2:
            self.direction = dir_list[2]

    def update_boundary(self,world):
        self.LEFT = 1
        self.RIGHT = world.get_width() - 2
        self.TOP = 1
        self.BOTTOM = world.get_height() - 2

    def do_move(self, world, friendly_unit, enemy_units):
        # increment turn count
        self.turn_count += 1

        # if unit is dead, stop making moves.
        if friendly_unit.status == 'DISABLED':
            print("Turn {0}: Disabled - skipping move.".format(str(self.turn_count)))
            self.target = None
            return


        if self.is_init == True:
            if self.turn_count == 1:

                self.update_boundary(world)
                self.update_dir(friendly_unit)

                friendly_unit.move(self.first_move)
                return
            elif self.turn_count == 2:
                friendly_unit.move(self.second_move)
                return
            elif self.turn_count > 2:
                self.units_taken += 1

            self.compare_distance(world, enemy_units, friendly_unit)

            if self.units_taken <= 2 * self.rec_len + 2:
                self.change_dir(self.dir_list)
                friendly_unit.move(self.dir_move(friendly_unit))
                return
            elif self.is_init:
                while friendly_unit.position != self.target_list[len(self.target_list) - 1]:
                    self.rec_2_move(friendly_unit)
                    friendly_unit.move(
                        world.path.get_next_point_in_shortest_path(friendly_unit.position, self.init_target))
                    return
                self.is_init = False

        print("here////////////")
        self.direction = 0


        # variables for friendly unit
        current_position = friendly_unit.position
        avoid = friendly_unit.snake
        enemy_distance = self.compute_enemy_distance(enemy_units, world, friendly_unit)
        print(enemy_distance)

        # variables for enemy unit
        closest_enemy_body = world.util.get_closest_enemy_body_from(current_position, None)



        # if unit reaches the target point and set target back to None
        if self.target is not None and current_position == self.target.position:
            self.target = None

        # if no target
        if self.target is None:
            # determine best route to create a square
            dir_1, dir_2 = self.square[self.direction].keys()
            point_1 = add_points(current_position, self.square[self.direction][dir_1])
            point_2 = add_points(current_position, self.square[self.direction][dir_2])
            if not world.is_within_bounds(point_1):
                self.target = world.position_to_tile_map[point_2]
            elif not world.is_within_bounds(point_2):
                self.target = world.position_to_tile_map[point_1]
            else:
                path_1 = world.path.get_shortest_path(current_position, point_1, avoid)
                path_2 = world.path.get_shortest_path(current_position, point_2, avoid)
                unfriendly_tiles_1 = [world.position_to_tile_map[point].is_friendly for point in path_1].count(
                    False)
                unfriendly_tiles_2 = [world.position_to_tile_map[point].is_friendly for point in path_2].count(
                    False)
                if unfriendly_tiles_1 > unfriendly_tiles_2:
                    self.target = world.position_to_tile_map[point_1]
                elif unfriendly_tiles_1 < unfriendly_tiles_2:
                    self.target = world.position_to_tile_map[point_2]
                else:
                    self.target = world.util.get_closest_neutral_territory_from(point_2, None)
            self.direction = not self.direction

        # go for the kill if safe and nearby
        if closest_enemy_body is not None:
            path_to_kill = world.path.get_shortest_path(current_position, closest_enemy_body.position, avoid)
            distance_to_kill = len(path_to_kill)
            # 2x because go there and back
            if all(2 * distance_to_kill > enemy_distance[enemy.uuid] for enemy in
                   enemy_units) and distance_to_kill <= 5:
                print("KILLL")
                self.target = closest_enemy_body

        # if unit is outside its territory
        if current_position not in friendly_unit.territory:
            closest_friendly_tile = world.util.get_closest_friendly_territory_from(current_position,
                                                                                   friendly_unit.snake)
            path_to_safety = world.path.get_shortest_path(current_position, closest_friendly_tile.position,
                                                          avoid)
            distance_to_safety = len(path_to_safety)
            print("safety {0}".format(distance_to_safety))
            for enemy in enemy_units:
                if enemy_distance[enemy.uuid] <= distance_to_safety:
                    print("RUNNNN")
                    self.target = closest_friendly_tile
                    break
        else:
            for enemy in enemy_units:
                if enemy_distance[enemy.uuid] <= 5:
                    print("DANGEROUS")
                    self.target = world.util.get_closest_neutral_territory_from(current_position, None)
                    avoid.add(enemy.position)

                    # set next move as the next point in the path to target
                next_move = world.path.get_shortest_path(current_position, self.target.position, avoid)[0]

                # move!
                friendly_unit.move(next_move)
                print("Turn {turn}: currently at {position}, making move to {target}.".format(
                    turn=str(self.turn_count),
                    position=str(friendly_unit.position),
                    target=str(self.target.position)
                ))





