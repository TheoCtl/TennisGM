import unittest

from src.sim.game_engine import GameEngine


class GameEngineMentalityAdvantageTests(unittest.TestCase):
    def test_advantage_cycle_shifts_form_range(self):
        player1 = {
            "id": "p1",
            "name": "Alpha",
            "skills": {"serve": 80, "forehand": 80, "backhand": 80, "speed": 80, "stamina": 80, "mental": 50},
            "mentality": "opportunist",
        }
        player2 = {
            "id": "p2",
            "name": "Beta",
            "skills": {"serve": 80, "forehand": 80, "backhand": 80, "speed": 80, "stamina": 80, "mental": 50},
            "mentality": "wildcard",
        }

        engine = GameEngine(player1, player2, "hard")

        self.assertEqual(engine.mentality_advantage_player_id, "p1")
        self.assertGreaterEqual(engine.p1["form_multiplier"], 1.0)
        self.assertLess(engine.p2["form_multiplier"], 1.0)

    def test_neutral_mentality_falls_back_to_normal_form(self):
        player1 = {
            "id": "p1",
            "name": "Alpha",
            "skills": {"serve": 80, "forehand": 80, "backhand": 80, "speed": 80, "stamina": 80, "mental": 50},
            "mentality": "neutral",
        }
        player2 = {
            "id": "p2",
            "name": "Beta",
            "skills": {"serve": 80, "forehand": 80, "backhand": 80, "speed": 80, "stamina": 80, "mental": 50},
            "mentality": "wildcard",
        }

        engine = GameEngine(player1, player2, "hard")

        self.assertIsNone(engine.mentality_advantage_player_id)
        self.assertGreaterEqual(engine.p1["form_multiplier"], 0.965)
        self.assertGreaterEqual(engine.p2["form_multiplier"], 0.965)


if __name__ == "__main__":
    unittest.main()
