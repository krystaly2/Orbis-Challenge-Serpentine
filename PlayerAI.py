from PythonClientAPI.game.PointUtils import *
from PythonClientAPI.game.Entities import FriendlyUnit, EnemyUnit, Tile
from PythonClientAPI.game.Enums import Team
from PythonClientAPI.game.World import World
from PythonClientAPI.game.TileUtils import TileUtils


class PlayerAI:

    def __init__(self):
        """ Initialize! """
        self.turn_count = 0             # game turn count
        self.target = None              # target to send unit to!
        self.square = ({"south": (-10, 0), "north": (10, 0)}, {"east": (0, 10), "west": (0, -10)})
        self.direction = 0

    def do_move(self, world, friendly_unit, enemy_units):
        """
        This method is called every turn by the game engine.
        Make sure you call friendly_unit.move(target) somewhere here!

        Below, you'll find a very rudimentary strategy to get you started.
        Feel free to use, or delete any part of the provided code - Good luck!

        :param world: world object (more information on the documentation)
            - world: contains information about the game map.
            - world.path: contains various pathfinding helper methods.
            - world.util: contains various tile-finding helper methods.
            - world.fill: contains various flood-filling helper methods.

        :param friendly_unit: FriendlyUnit object
        :param enemy_units: list of EnemyUnit objects
        """
        # variables for friendly unit
        current_position = friendly_unit.position
        avoid = friendly_unit.snake

        # variables for enemy unit
        closest_enemy_body = world.util.get_closest_enemy_body_from(current_position, None)
        enemy_distance = {}
        for enemy in enemy_units:
            enemy_distance[enemy.uuid] = min([world.path.get_taxi_cab_distance(enemy.position, body_position) for body_position in friendly_unit.snake])

        # increment turn count
        self.turn_count += 1

        # if unit is dead, stop making moves.
        if friendly_unit.status == 'DISABLED':
            print("Turn {0}: Disabled - skipping move.".format(str(self.turn_count)))
            self.target = None
            return

        # if unit reaches the target point, reverse outbound boolean and set target back to None
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
                unfriendly_tiles_1 = [world.position_to_tile_map[point].is_friendly for point in path_1].count(False)
                unfriendly_tiles_2 = [world.position_to_tile_map[point].is_friendly for point in path_2].count(False)
                if unfriendly_tiles_1 > unfriendly_tiles_2:
                    self.target = world.position_to_tile_map[point_1]
                elif unfriendly_tiles_1 < unfriendly_tiles_2:
                    self.target = world.position_to_tile_map[point_2]
                else:
                    self.target = world.util.get_closest_neutral_territory_from(point_2, None)
            self.direction = 0 if self.direction else 1

        # go for the kill if safe and nearby
        if closest_enemy_body is not None:
            path_to_kill = world.path.get_shortest_path(current_position, closest_enemy_body.position, avoid)
            distance_to_kill = len(path_to_kill)
            # 2x because go there and back
            if all(2*distance_to_kill > enemy_distance[enemy.uuid] for enemy in enemy_units) and distance_to_kill <= 5:
                print("KILLL")
                self.target = closest_enemy_body

        # if unit is outside its territory
        if current_position not in friendly_unit.territory:
            closest_friendly_tile = world.util.get_closest_friendly_territory_from(current_position, friendly_unit.snake)
            path_to_safety = world.path.get_shortest_path(current_position, closest_friendly_tile.position, avoid)
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

