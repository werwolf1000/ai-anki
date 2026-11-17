"""Smoke test итогового проекта; ML-зависимости устанавливаются отдельно от сервера."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HAS_ML = all(importlib.util.find_spec(name) is not None for name in ("torch", "sklearn", "pandas"))


@unittest.skipUnless(HAS_ML, "Нужны examples/python_neural_network/requirements.txt")
class NeuralNetworkProjectTest(unittest.TestCase):
    def test_train_save_load_and_predict_on_cpu(self):
        from examples.python_neural_network.train import predict, train

        with TemporaryDirectory() as directory:
            output = Path(directory)
            metrics = train(output, epochs=80, seed=42)
            self.assertEqual((metrics["train_size"], metrics["validation_size"], metrics["test_size"]), (90, 30, 30))
            self.assertGreater(metrics["test_accuracy"], metrics["baseline_accuracy"])
            self.assertGreaterEqual(metrics["test_accuracy"], 0.75)
            history = json.loads((output / "history.json").read_text(encoding="utf-8"))
            self.assertLess(history[-1]["train_loss"], history[0]["train_loss"])
            checkpoint = output / "model.pt"
            values = [5.1, 3.5, 1.4, 0.2]
            result = predict(checkpoint, values)
            self.assertEqual(result["class"], "setosa")
            self.assertAlmostEqual(sum(result["probabilities"].values()), 1, places=5)
            self.assertEqual(result, predict(checkpoint, values))
            with self.assertRaises(ValueError):
                predict(checkpoint, [1, 2, 3])
            with self.assertRaises(ValueError):
                predict(checkpoint, [1, 2, 3, float("nan")])


if __name__ == "__main__":
    unittest.main()
