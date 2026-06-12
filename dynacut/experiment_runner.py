import os
import json
import time
import logging
from typing import List, Dict, Any, Callable, Optional
import numpy as np

logger = logging.getLogger(__name__)

class ExperimentRunner:
    """A reusable harness for running multi-seed statistical quantum experiments."""
    
    def __init__(
        self, 
        experiment_name: str,
        seeds: List[int] = None,
        results_dir: str = "results"
    ):
        self.experiment_name = experiment_name
        self.seeds = seeds if seeds is not None else [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Auto-load config.yaml
        self.global_config = {}
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "experiments", "config.yaml")
        if os.path.exists(config_path):
            import yaml
            with open(config_path, "r") as f:
                self.global_config = yaml.safe_load(f)
                if "experiment_parameters" in self.global_config and "seeds" in self.global_config["experiment_parameters"] and seeds is None:
                    self.seeds = self.global_config["experiment_parameters"]["seeds"]
        
    def run(self, experiment_fn: Callable[[int, Dict[str, Any]], Dict[str, Any]], config: Dict[str, Any] = None) -> Dict[str, Any]:
        if config is None:
            config = {}
        # Merge global config into passed config
        merged_config = {**self.global_config, **config}
        """
        Run the experiment function over all seeds.
        
        Parameters
        ----------
        experiment_fn : callable
            A function that takes (seed, config) and returns a flat dictionary of results.
        config : dict
            Configuration parameters to pass to the experiment.
            
        Returns
        -------
        dict
            A dictionary containing both the raw results and summary statistics.
        """
        raw_results = []
        
        # Check if already completed or partially completed
        stats_path = os.path.join(self.results_dir, f"{self.experiment_name}_stats.json")
        raw_path = os.path.join(self.results_dir, f"{self.experiment_name}_raw.json")
        
        completed_seeds = set()
        if os.path.exists(raw_path) and os.path.getsize(raw_path) > 10:
            try:
                with open(raw_path, 'r') as f:
                    raw_results = json.load(f)
                completed_seeds = {r.get("seed", -1) for r in raw_results}
            except json.JSONDecodeError:
                logger.warning(f"Failed to load existing results for '{self.experiment_name}', starting fresh.")
                raw_results = []
                
        if os.path.exists(stats_path) and os.path.getsize(stats_path) > 10 and len(completed_seeds) == len(self.seeds):
            logger.info(f"Experiment '{self.experiment_name}' already fully completed. Skipping.")
            with open(stats_path, 'r') as f:
                stats_res = json.load(f)
            return {"raw": raw_results, "stats": stats_res}
        
        logger.info(f"Starting experiment '{self.experiment_name}' with {len(self.seeds)} seeds.")
        t_start = time.time()
        
        for i, seed in enumerate(self.seeds):
            if seed in completed_seeds:
                logger.info(f"  [Seed {seed}] Already completed. Skipping. ({i+1}/{len(self.seeds)})")
                continue
                
            logger.info(f"  [Seed {seed}] Running... ({i+1}/{len(self.seeds)})")
            
            try:
                # Add seed to config for convenience
                run_config = config.copy()
                run_config["seed"] = seed
                
                # Execute the experiment
                result = experiment_fn(seed, run_config)
                
                # Ensure seed is recorded in the result
                result["seed"] = seed
                raw_results.append(result)
                
                # Incrementally save to prevent data loss on crash
                with open(raw_path, 'w') as f:
                    json.dump(raw_results, f, indent=2)
                
            except Exception as e:
                logger.error(f"  [Seed {seed}] Failed with error: {e}", exc_info=True)
                # We could append a failure record or skip. For rigor, we should log but continue.
                
        t_total = time.time() - t_start
        logger.info(f"Experiment '{self.experiment_name}' completed in {t_total:.2f}s.")
        
        # Calculate statistics
        stats = self._calculate_statistics(raw_results)
        
        # Save results
        raw_path = os.path.join(self.results_dir, f"{self.experiment_name}_raw.json")
        stats_path = os.path.join(self.results_dir, f"{self.experiment_name}_stats.json")
        
        with open(raw_path, 'w') as f:
            json.dump(raw_results, f, indent=2)
            
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
            
        logger.info(f"Results saved to {raw_path} and {stats_path}")
        
        return {
            "raw": raw_results,
            "stats": stats
        }
        
    def _calculate_statistics(self, raw_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate mean, std, min, max, median for numeric fields."""
        if not raw_results:
            return {}
            
        # Group values by key
        grouped = {}
        for res in raw_results:
            for k, v in res.items():
                if k == "seed":
                    continue
                if isinstance(v, (int, float, np.number)) and not isinstance(v, bool):
                    if k not in grouped:
                        grouped[k] = []
                    # Filter out NaNs for stats
                    if not np.isnan(v):
                        grouped[k].append(float(v))
                
        # Compute stats
        stats = {}
        for k, values in grouped.items():
            if not values:
                continue
            arr = np.array(values)
            n = len(arr)
            mean = float(np.mean(arr))
            std = float(np.std(arr))
            
            # 95% Confidence Interval (Normal Approximation)
            ci_95 = 1.96 * (std / np.sqrt(n)) if n > 0 else 0.0
            
            stats[k] = {
                "mean": mean,
                "std": std,
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "median": float(np.median(arr)),
                "count": n,
                "ci_95": float(ci_95)
            }
            
        return stats
