"""Reinforcement Learning trainer for dynamic fraud decision optimization."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd

from configs import AppConfig

LOGGER = logging.getLogger("aegis.training.rl")

try:
    import gymnasium as gym
    from gymnasium import spaces
    RL_GYM_AVAILABLE = True
except ImportError:
    RL_GYM_AVAILABLE = False
    LOGGER.warning("Gymnasium not available for RL training")
    gym = None  # type: ignore
    spaces = None  # type: ignore


if RL_GYM_AVAILABLE:
    class FraudDecisionEnv(gym.Env):
        """
        Gymnasium environment for fraud decision optimization.
        
        The agent learns to make optimal decisions (Allow/Flag/Block) based on
        transaction features and model predictions.
        """
        
        metadata = {"render_modes": ["human"], "render_fps": 30}
        
        def __init__(self, transactions: pd.DataFrame, config: AppConfig):
            super().__init__()
            self.transactions = transactions.reset_index(drop=True)
            self.config = config
            self.current_idx = 0
            self.max_steps = len(transactions)
            
            # Action space: 0=Allow, 1=Flag for review, 2=Block
            self.action_space = spaces.Discrete(3)
            
            # Observation space: simplified transaction features
            # Using 20 key features for faster training
            self.observation_space = spaces.Box(
                low=-10.0, high=10.0, 
                shape=(20,),
                dtype=np.float32
            )
            
            # Reward weights
            self.reward_correct_block = 100.0
            self.reward_correct_allow = 1.0
            self.reward_false_positive = -50.0
            self.reward_false_negative = -200.0
            self.reward_correct_flag = 50.0
            self.reward_incorrect_flag = -10.0
        
        def _get_obs(self) -> np.ndarray:
            """Extract observation from current transaction."""
            if self.current_idx >= len(self.transactions):
                return np.zeros(20, dtype=np.float32)
            
            txn = self.transactions.iloc[self.current_idx]
            
            # Extract key features (normalize/standardize as needed)
            obs = np.array([
                txn.get("amount", 0) / 10000.0,  # Normalize amount
                txn.get("log_amount", 0),
                txn.get("risk_score", 0),
                txn.get("risk_score_gap", 0),
                txn.get("anomaly_score", 0),
                txn.get("relative_amount_to_avg", 0),
                txn.get("amount_to_daily_limit_ratio", 0),
                txn.get("amount_to_monthly_limit_ratio", 0),
                txn.get("known_device", 0),
                txn.get("device_trust_gap", 0),
                txn.get("hesitation_indicators", 0),
                txn.get("typing_pattern_anomaly", 0),
                txn.get("new_payee_flag", 0),
                txn.get("authentication_failures", 0),
                txn.get("is_night", 0),
                txn.get("is_weekend", 0),
                txn.get("sin_hour", 0),
                txn.get("cos_hour", 0),
                txn.get("vulnerability_score", 0) / 100.0,
                txn.get("credit_score", 0) / 850.0,
            ], dtype=np.float32)
            
            return obs
        
        def _get_info(self) -> Dict:
            """Return auxiliary information."""
            return {
                "current_idx": self.current_idx,
                "is_fraud": int(self.transactions.iloc[self.current_idx].get("is_fraud", 0)) if self.current_idx < len(self.transactions) else 0,
            }
        
        def reset(self, seed: int | None = None, options: Dict | None = None):
            """Reset environment to initial state."""
            super().reset(seed=seed)
            self.current_idx = 0
            if seed is not None:
                np.random.seed(seed)
                # Shuffle transactions for variety
                self.transactions = self.transactions.sample(frac=1, random_state=seed).reset_index(drop=True)
            
            observation = self._get_obs()
            info = self._get_info()
            return observation, info
        
        def step(self, action: int):
            """Execute action and return next state, reward, done, info."""
            if self.current_idx >= len(self.transactions):
                return self._get_obs(), 0.0, True, False, self._get_info()
            
            txn = self.transactions.iloc[self.current_idx]
            is_fraud = int(txn.get("is_fraud", 0))
            
            # Calculate reward based on action and ground truth
            if action == 2:  # Block
                reward = self.reward_correct_block if is_fraud else self.reward_false_positive
            elif action == 1:  # Flag for review
                reward = self.reward_correct_flag if is_fraud else self.reward_incorrect_flag
            else:  # Allow (action == 0)
                reward = self.reward_correct_allow if not is_fraud else self.reward_false_negative
            
            self.current_idx += 1
            terminated = self.current_idx >= self.max_steps
            truncated = False
            
            observation = self._get_obs()
            info = self._get_info()
            
            return observation, reward, terminated, truncated, info
        
        def render(self):
            """Render environment (not implemented)."""
            pass
        
        def close(self):
            """Clean up resources."""
            pass


def train_rl_policy(transactions: pd.DataFrame, config: AppConfig) -> Dict[str, Path]:
    """
    Train RL policy for fraud decision optimization.
    
    Note: This is a simplified implementation. For production, consider using
    stable-baselines3 or similar libraries with PPO/DQN algorithms.
    
    Args:
        transactions: Transaction data
        config: Application configuration
        
    Returns:
        Dictionary of artifact paths
    """
    if not RL_GYM_AVAILABLE:
        LOGGER.warning("Gymnasium not available, skipping RL training")
        return {}
    
    LOGGER.info("Training RL policy for fraud decisions")
    
    try:
        # Create environment
        env = FraudDecisionEnv(transactions, config)
        
        # Simple random policy for demonstration
        # In production, replace with PPO/DQN from stable-baselines3
        LOGGER.info("Training simple random policy (placeholder for PPO/DQN)")
        
        # Collect some statistics
        num_episodes = 10
        episode_rewards = []
        
        for episode in range(num_episodes):
            obs, info = env.reset(seed=config.random_state + episode)
            episode_reward = 0
            done = False
            
            while not done:
                # Random action (placeholder)
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                done = terminated or truncated
            
            episode_rewards.append(episode_reward)
            LOGGER.info("Episode %d: Total Reward = %.2f", episode + 1, episode_reward)
        
        avg_reward = np.mean(episode_rewards)
        LOGGER.info("Average episode reward: %.2f", avg_reward)
        
        # Save policy artifacts (placeholder)
        artifact_dir = config.output_dir / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        policy_path = artifact_dir / "aegis_rl_policy.pkl"
        config_path = artifact_dir / "aegis_rl_config.json"
        metrics_path = config.output_dir / "rl_metrics.json"
        
        # Save simple policy config
        policy_config = {
            "env_name": "FraudDecisionEnv",
            "action_space": 3,
            "observation_space": 20,
            "reward_weights": {
                "correct_block": env.reward_correct_block,
                "correct_allow": env.reward_correct_allow,
                "false_positive": env.reward_false_positive,
                "false_negative": env.reward_false_negative,
            }
        }
        
        joblib.dump(policy_config, policy_path)
        config_path.write_text(json.dumps(policy_config, indent=2))
        
        metrics = {
            "avg_episode_reward": float(avg_reward),
            "num_episodes": num_episodes,
            "policy_type": "random_baseline",
        }
        metrics_path.write_text(json.dumps(metrics, indent=2))
        
        LOGGER.info("RL policy training completed (baseline)")
        
        return {
            "rl_policy": policy_path,
            "rl_config": config_path,
            "rl_metrics": metrics_path,
        }
        
    except Exception as exc:
        LOGGER.error("RL training failed: %s", exc, exc_info=True)
        return {}

